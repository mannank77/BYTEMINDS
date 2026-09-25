"""
BIS Standards Retriever — Hybrid BM25 + Semantic Embeddings
============================================================
Two retrieval modes depending on what is available at runtime:

  Mode A  (hybrid)  — BM25 score  +  cosine similarity from a local
                       sentence-transformers model, fused with a weighted sum.
                       Activated automatically when sentence-transformers is
                       installed and the embedding cache exists.

  Mode B  (BM25-only) — identical to the original retriever; used as a
                         graceful fallback so inference.py always works.

Building the embedding cache (one-time, ~30 s on CPU):
    python -c "from src.retriever import get_retriever; get_retriever()"

Or run preprocess.py with --build-embeddings to do it as part of indexing.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path


# ── Constants ───────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # ~90 MB, CPU-friendly
EMBEDDING_CACHE  = "data/embeddings.npy"                       # precomputed vectors

# Fusion weights  (must sum to 1.0)
BM25_WEIGHT      = 0.40
SEMANTIC_WEIGHT  = 0.60

# BM25 hyperparameters (tuned for SP-21 chunk lengths)
BM25_K1 = 1.4
BM25_B  = 0.70

# Title / standard-id boost (BM25 phase)
TITLE_BOOST    = 2.8
MATERIAL_BOOST = 5.0
MATERIAL_PENALTY = -1.5
EXPLICIT_BOOST = 100.0

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "both", "by", "for",
    "from", "i", "in", "is", "it", "of", "or", "our", "the", "their",
    "to", "used", "using", "we", "what", "which", "with",
}

QUERY_EXPANSIONS: dict[str, str] = {
    "33 grade":            "ordinary portland cement 33 grade opc chemical physical",
    "43 grade":            "ordinary portland cement 43 grade opc",
    "53 grade":            "ordinary portland cement 53 grade opc",
    "aggregate":           "coarse fine aggregate aggregates natural sources concrete",
    "calcined clay":       "portland pozzolana cement part 2 calcined clay based",
    "fly ash":             "portland pozzolana cement part 1 fly ash based",
    "slag cement":         "portland slag cement",
    "white portland":      "white portland cement architectural decorative",
    "rapid hardening":     "rapid hardening portland cement",
    "hydrophobic":         "hydrophobic portland cement",
    "sulphate resisting":  "sulphate resisting portland cement",
    "supersulphated":      "supersulphated cement marine aggressive sulphate",
    "masonry cement":      "masonry cement mortars masonry not structural concrete",
    "masonry mortars":     "sand masonry mortars",
    "precast concrete pipes": "precast concrete pipes with without reinforcement",
    "water mains":         "pipes pressure non pressure water mains",
    "hollow and solid lightweight":
                           "concrete masonry units part 2 hollow solid lightweight",
    "lightweight concrete masonry blocks":
                           "concrete masonry units part 2 hollow solid lightweight",
    "concrete masonry blocks": "concrete masonry units hollow solid blocks",
    "corrugated and semi-corrugated":
                           "corrugated semi corrugated asbestos cement sheets roofing",
    "roofing and cladding": "sheets roofing cladding",
    "reinforcement":       "steel bar rebar concrete reinforcement",
    "structural steel":    "structural steel section beam column",
    "waterproof":          "waterproofing dampproofing membrane bitumen",
    "insulation":          "thermal insulation material board",
    "pvc pipe":            "plastic pipe pvc tube",
    "glass":               "glass glazing float tempered",
    "door":                "door shutter frame wood steel",
    "window":              "window frame shutter glass",
    "tile":                "floor wall tile ceramic burnt clay",
    "paint":               "paint coating finish varnish",
    "bolt":                "bolt nut fastener threaded",
    "wire":                "wire rope strand electrical",
    "aluminium":           "aluminium alloy light metal section",
    "gypsum":              "gypsum plaster board building",
    "lime":                "building lime mortar hydrated",
    "bitumen":             "bitumen tar waterproofing road",
    "sanitary":            "sanitary appliance wash basin toilet seat",
}

MATERIAL_TERMS = {
    "aggregate", "aggregates", "asbestos", "bitumen", "cement", "concrete",
    "corrugated", "gypsum", "lime", "lightweight", "masonry", "pozzolana",
    "precast", "slag", "steel", "supersulphated", "timber", "white",
    "reinforcement", "rebar", "insulation", "waterproofing", "aluminium",
    "plastic", "glass", "tile", "door", "window", "wire", "bolt", "paint",
}


# ── Text helpers ────────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    return [
        t for t in re.findall(r"[a-z]+|\d+(?:\.\d+)?", text.lower())
        if t not in STOPWORDS
    ]


def normalize_standard(standard: str) -> str:
    s = re.sub(r"\s+", " ", str(standard).strip()).upper()
    s = re.sub(r"\(\s*PART\s*(\d+)\s*\)", r"(Part \1)", s, flags=re.I)
    s = re.sub(r"\s*:\s*", ": ", s)
    s = re.sub(r"^IS\s*", "IS ", s)
    return s


# ── Retriever ───────────────────────────────────────────────────────────────────

class BISRetriever:
    """
    Hybrid retriever.  Falls back to BM25-only if sentence-transformers or
    the embedding cache is not available.
    """

    def __init__(self, data_path: str | None = None, embedding_cache: str | None = None):
        root = Path(__file__).resolve().parents[1]
        self.data_path = Path(data_path) if data_path else root / "data" / "processed_data.json"
        self.cache_path = Path(embedding_cache) if embedding_cache else root / EMBEDDING_CACHE

        self.documents: list[dict] = json.loads(
            self.data_path.read_text(encoding="utf-8")
        )
        self._prepare_bm25()
        self._load_embeddings()          # no-op if unavailable

    # ── BM25 setup ──────────────────────────────────────────────────────────────

    def _prepare_bm25(self) -> None:
        self.doc_tokens: list[list[str]] = []
        self.doc_term_counts: list[Counter] = []
        document_frequency: Counter = Counter()

        for doc in self.documents:
            standard = normalize_standard(doc.get("standard", ""))
            title = doc.get("title") or self._title_from_text(doc.get("text", ""))
            doc["standard"] = standard
            doc["title"] = title

            category = doc.get("category", "")

            # Weighted concatenation: standard id and title repeated for boost
            weighted_text = " ".join([
                (standard + " ") * 8,
                (title + " ") * 12,
                (category + " ") * 4,
                doc.get("text", ""),
            ])
            tokens = tokenize(weighted_text)
            counts = Counter(tokens)
            self.doc_tokens.append(tokens)
            self.doc_term_counts.append(counts)
            document_frequency.update(set(tokens))

        self.num_docs = len(self.documents)
        self.avg_doc_len = (
            sum(len(t) for t in self.doc_tokens) / max(self.num_docs, 1)
        )
        self.idf = {
            term: math.log(1 + (self.num_docs - freq + 0.5) / (freq + 0.5))
            for term, freq in document_frequency.items()
        }

    def _title_from_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        match = re.search(
            r"IS\s+\d+(?:\s*\(\s*PART\s*\d+\s*\))?\s*:\s*\d{4}\s+(.+)",
            text, flags=re.I,
        )
        if not match:
            return ""
        title = re.split(
            r"\s+(?:\([^)]*Revision\)|1\.\s*Scope|Scope\s*[—-]|1\.\s|2\.\s"
            r"|TABLE\s+|Note\s*[—-])",
            match.group(1), maxsplit=1, flags=re.I,
        )[0]
        return re.sub(r"\s+", " ", title).strip(" -—:")[:250]

    # ── Embedding setup ─────────────────────────────────────────────────────────

    def _load_embeddings(self) -> None:
        """Try to load precomputed embeddings + the model for query encoding."""
        self.embeddings = None
        self.embed_model = None

        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("[retriever] sentence-transformers not installed -> BM25-only mode")
            return

        if not self.cache_path.exists():
            print(f"[retriever] No embedding cache at {self.cache_path} -> building ...")
            self._build_and_save_embeddings()
            return

        try:
            self.embeddings = np.load(str(self.cache_path))
            self.embed_model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"[retriever] Loaded {len(self.embeddings)} embeddings -> hybrid mode")
        except Exception as exc:
            print(f"[retriever] Could not load embeddings ({exc}) -> BM25-only mode")
            self.embeddings = None

    def _build_and_save_embeddings(self) -> None:
        """Encode all documents and save as .npy (call once, ~30 s on CPU)."""
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return

        model = SentenceTransformer(EMBEDDING_MODEL)

        # Build a rich sentence per standard for embedding
        sentences = []
        for doc in self.documents:
            sentence = " ".join(filter(None, [
                doc.get("standard", ""),
                doc.get("title", ""),
                doc.get("category", ""),
                doc.get("text", "")[:512],     # cap to avoid very long inputs
            ]))
            sentences.append(sentence)

        print(f"[retriever] Encoding {len(sentences)} standards ...")
        vecs = model.encode(sentences, batch_size=64, show_progress_bar=True,
                            normalize_embeddings=True)

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(self.cache_path), vecs)
        self.embeddings = vecs
        self.embed_model = model
        print(f"[retriever] Saved embeddings to {self.cache_path}")

    # ── Query helpers ───────────────────────────────────────────────────────────

    def _expanded_query(self, query: str) -> str:
        lowered = query.lower()
        additions = [v for k, v in QUERY_EXPANSIONS.items() if k in lowered]
        return " ".join([query, *additions])

    def _explicit_standard_matches(self, query: str) -> set[int]:
        matches = re.findall(
            r"\bIS\s*[:\-]?\s*(\d{2,5})(?:\s*\(?\s*Part\s*(\d+)\s*\)?)?"
            r"\s*[:\-]?\s*(\d{4})?",
            query, flags=re.I,
        )
        explicit: set[int] = set()
        for number, part, year in matches:
            wanted = f"is{number}"
            if part:
                wanted += f"(part{part})"
            for i, doc in enumerate(self.documents):
                key = doc["standard"].lower().replace(" ", "")
                if wanted in key and (not year or year in key):
                    explicit.add(i)
        return explicit

    # ── BM25 scoring ────────────────────────────────────────────────────────────

    def _bm25_score(self, query_counts: Counter, doc_index: int) -> float:
        counts  = self.doc_term_counts[doc_index]
        doc_len = len(self.doc_tokens[doc_index])
        score   = 0.0
        for token, qcount in query_counts.items():
            freq = counts.get(token, 0)
            if not freq:
                continue
            denom  = freq + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avg_doc_len)
            score += (
                self.idf.get(token, 0.0)
                * freq * (BM25_K1 + 1) / denom
                * (1 + 0.10 * (qcount - 1))
            )
        return score

    # ── Main retrieve ────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        expanded        = self._expanded_query(query)
        query_tokens    = tokenize(expanded)
        query_counts    = Counter(query_tokens)
        explicit_matches = self._explicit_standard_matches(query)

        # ── BM25 phase ──────────────────────────────────────────────────────────
        bm25_scores: list[float] = []
        for i, doc in enumerate(self.documents):
            score = self._bm25_score(query_counts, i)
            title_tokens = set(tokenize(f"{doc['standard']} {doc.get('title', '')}"))
            score += TITLE_BOOST * sum(
                1 for t in set(query_tokens) if len(t) > 2 and t in title_tokens
            )
            for token in MATERIAL_TERMS.intersection(query_tokens):
                score += MATERIAL_BOOST if token in title_tokens else MATERIAL_PENALTY
            if i in explicit_matches:
                score += EXPLICIT_BOOST
            bm25_scores.append(score)

        # ── Semantic phase (skip if unavailable) ────────────────────────────────
        if self.embeddings is not None and self.embed_model is not None:
            import numpy as np

            q_vec = self.embed_model.encode(
                [expanded], normalize_embeddings=True
            )[0]                                         # shape (dim,)
            sem_scores = (self.embeddings @ q_vec).tolist()   # cosine sim

            # Min-max normalise each score list to [0, 1] before fusing
            def _norm(scores: list[float]) -> list[float]:
                lo, hi = min(scores), max(scores)
                span = hi - lo or 1.0
                return [(s - lo) / span for s in scores]

            bm25_n = _norm(bm25_scores)
            sem_n  = _norm(sem_scores)

            combined = [
                BM25_WEIGHT * b + SEMANTIC_WEIGHT * s
                for b, s in zip(bm25_n, sem_n)
            ]

            # Re-apply explicit-match override after fusion
            for i in explicit_matches:
                combined[i] += EXPLICIT_BOOST

            scored = sorted(enumerate(combined), key=lambda x: x[1], reverse=True)
        else:
            # BM25-only fallback
            scored = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)

        return [
            {
                "standard": self.documents[i]["standard"],
                "title":    self.documents[i].get("title", ""),
                "score":    score,
            }
            for i, score in scored[:top_k]
        ]


# ── Elasticsearch Retriever ──────────────────────────────────────────────────────

ES_HOST = "http://localhost:9200"
ALIAS_NAME = "bis_standards_active"


class ElasticsearchRetriever:
    """
    Elasticsearch Hybrid Retriever (Lucene BM25 + HNSW Cosine Dense Vectors).
    Gracefully falls back to in-memory BISRetriever if Elasticsearch is unreachable.
    """

    def __init__(self, es_host: str = ES_HOST, alias_name: str = ALIAS_NAME):
        self.es_host = es_host
        self.alias_name = alias_name
        self.fallback: BISRetriever | None = None
        self.embed_model = None

        try:
            from elasticsearch import Elasticsearch
            self.es = Elasticsearch(es_host, request_timeout=2.0)
        except Exception:
            self.es = None

        try:
            from sentence_transformers import SentenceTransformer
            self.embed_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception:
            self.embed_model = None

    def is_available(self) -> bool:
        if self.es is None:
            return False
        try:
            return bool(self.es.ping()) and bool(self.es.indices.exists_alias(name=self.alias_name))
        except Exception:
            return False

    def _fallback_retriever(self) -> BISRetriever:
        if self.fallback is None:
            self.fallback = BISRetriever()
            if self.embed_model is not None and self.fallback.embed_model is None:
                self.fallback.embed_model = self.embed_model
        return self.fallback

    def _extract_explicit_standards(self, query: str) -> list[str]:
        """Extract explicit standard codes (e.g. IS 383, IS 1489 Part 1)."""
        matches = re.findall(
            r"\bIS\s*[:\-]?\s*(\d{2,5})(?:\s*\(?\s*Part\s*(\d+)\s*\)?)?",
            query,
            flags=re.I,
        )
        explicit_codes = []
        for number, part in matches:
            if part:
                explicit_codes.append(f"IS {number} (Part {part})")
            else:
                explicit_codes.append(f"IS {number}")
        return explicit_codes

    def _expanded_query(self, query: str) -> str:
        lowered = query.lower()
        additions = [v for k, v in QUERY_EXPANSIONS.items() if k in lowered]
        return " ".join([query, *additions])

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.is_available():
            return self._fallback_retriever().retrieve(query, top_k=top_k)

        expanded = self._expanded_query(query)
        explicit_codes = self._extract_explicit_standards(query)

        should_clauses: list[dict] = [
            {
                "multi_match": {
                    "query": expanded,
                    "fields": ["standard^8.0", "title^4.0", "category^2.0", "text^1.0"],
                    "boost": BM25_WEIGHT,
                }
            }
        ]

        # Explicit code boost (+100.0)
        for code in explicit_codes:
            should_clauses.append({
                "match_phrase": {
                    "standard": {
                        "query": code,
                        "boost": EXPLICIT_BOOST,
                    }
                }
            })

        body: dict = {
            "query": {
                "bool": {
                    "should": should_clauses
                }
            },
            "size": top_k
        }

        # Add kNN dense vector clause if SentenceTransformer model is available
        if self.embed_model is not None:
            q_vec = self.embed_model.encode([expanded], normalize_embeddings=True)[0].tolist()
            body["knn"] = {
                "field": "embedding",
                "query_vector": q_vec,
                "k": max(top_k * 3, 10),
                "num_candidates": 50,
                "boost": SEMANTIC_WEIGHT,
            }

        try:
            res = self.es.search(index=self.alias_name, body=body)
            hits = res.get("hits", {}).get("hits", [])
            return [
                {
                    "standard": hit["_source"]["standard"],
                    "title": hit["_source"].get("title", ""),
                    "score": hit.get("_score", 0.0),
                }
                for hit in hits
            ]
        except Exception as exc:
            print(f"[retriever] Elasticsearch query error ({exc}) -> falling back to in-memory")
            return self._fallback_retriever().retrieve(query, top_k=top_k)


# ── Singleton ────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_retriever():
    es_retriever = ElasticsearchRetriever()
    if es_retriever.is_available():
        print("[retriever] Using ElasticsearchRetriever ('bis_standards_active')")
        return es_retriever
    print("[retriever] Using in-memory BISRetriever (fallback mode)")
    return BISRetriever()