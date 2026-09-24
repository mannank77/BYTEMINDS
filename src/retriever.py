"""
BIS Standards Retriever — Two-Stage Hybrid Retrieval with Cross-Encoder Reranking
==================================================================================
Architecture
------------
  Stage 1  (Retrieval — High Recall)
     BM25 lexical scoring  +  Dense cosine similarity from BGE-M3 embeddings,
     fused with a weighted sum.  Retrieves a broad pool of candidate documents
     (default: top 50).

  Stage 2  (Reranking — High Precision)
     A Cross-Encoder model (BGE-Reranker-v2-M3) jointly scores each
     (query, document) pair for fine-grained relevance.  Returns the final
     top-K results with dramatically improved precision.

Graceful Fallbacks
------------------
  - If sentence-transformers is missing → BM25-only (no embeddings, no reranker).
  - If embedding cache is missing → auto-builds it on first launch (~60 s on CPU).
  - If cross-encoder fails to load → skips Stage 2 and returns Stage 1 results.

Building the embedding cache (one-time):
    python -c "from src.retriever import get_retriever; get_retriever()"
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path


# ── Constants ───────────────────────────────────────────────────────────────────

# Stage 1: Dense Bi-Encoder (BGE-M3 — multilingual, 100+ languages incl. Hindi)
EMBEDDING_MODEL  = "BAAI/bge-m3"
EMBEDDING_CACHE  = "data/embeddings_bge_m3.npy"

# Stage 2: Cross-Encoder Reranker (BGE-Reranker-v2-M3 — multilingual)
RERANKER_MODEL   = "BAAI/bge-reranker-v2-m3"

# Stage 1 candidate pool size (fed to Stage 2)
STAGE1_POOL_SIZE = 50

# Fusion weights for Stage 1 (must sum to 1.0)
BM25_WEIGHT      = 0.35
SEMANTIC_WEIGHT  = 0.65

# BM25 hyperparameters (tuned for SP-21 chunk lengths)
BM25_K1 = 1.4
BM25_B  = 0.70

# Title / standard-id boost (BM25 phase)
TITLE_BOOST      = 2.8
MATERIAL_BOOST   = 5.0
MATERIAL_PENALTY = -1.5
EXPLICIT_BOOST   = 100.0

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
    Two-stage hybrid retriever:
      Stage 1 — BM25 + BGE-M3 dense embeddings → top STAGE1_POOL_SIZE candidates
      Stage 2 — BGE-Reranker-v2-M3 cross-encoder → final top-K with max precision

    Falls back gracefully:
      - No sentence-transformers → BM25-only
      - No cross-encoder       → Stage 1 results returned directly
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
        self._load_reranker()            # no-op if unavailable

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

    # ── Embedding setup (Stage 1 — Dense Retrieval) ─────────────────────────────

    def _load_embeddings(self) -> None:
        """Try to load precomputed BGE-M3 embeddings + the model for query encoding."""
        self.embeddings = None
        self.embed_model = None

        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            
            if not self.cache_path.exists():
                print(f"[retriever] No embedding cache at {self.cache_path} -> building ...")
                self._build_and_save_embeddings()
                return

            self.embeddings = np.load(str(self.cache_path))
            self.embed_model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"[retriever] Loaded {len(self.embeddings)} BGE-M3 embeddings -> hybrid mode")
        except ImportError:
            print("[retriever] sentence-transformers not installed -> BM25-only mode")
        except Exception as exc:
            print(f"[retriever] Could not load embeddings ({exc}) -> BM25-only mode")
            self.embeddings = None

    def _build_and_save_embeddings(self) -> None:
        """Encode all documents with BGE-M3 and save as .npy (one-time, ~60 s on CPU)."""
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            
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

            print(f"[retriever] Encoding {len(sentences)} standards with {EMBEDDING_MODEL} ...")
            vecs = model.encode(sentences, batch_size=32, show_progress_bar=True,
                                normalize_embeddings=True)

            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(str(self.cache_path), vecs)
            self.embeddings = vecs
            self.embed_model = model
            print(f"[retriever] Saved BGE-M3 embeddings to {self.cache_path}")
        except ImportError:
            pass

    # ── Cross-Encoder Reranker setup (Stage 2 — Precision) ──────────────────────

    def _load_reranker(self) -> None:
        """Load the BGE-Reranker-v2-M3 cross-encoder for Stage 2 reranking."""
        self.reranker = None

        try:
            from sentence_transformers import CrossEncoder
            self.reranker = CrossEncoder(RERANKER_MODEL)
            print(f"[retriever] Loaded cross-encoder reranker: {RERANKER_MODEL}")
        except ImportError:
            print("[retriever] CrossEncoder not available -> skipping Stage 2 reranking")
        except Exception as exc:
            print(f"[retriever] Could not load reranker ({exc}) -> skipping Stage 2")
            self.reranker = None

    # ── Query helpers ───────────────────────────────────────────────────────────

    def _expanded_query(self, query: str) -> str:
        # 1. Vernacular / Hindi / Hinglish translation & domain normalization
        try:
            from src.vernacular_normalizer import get_vernacular_normalizer
            v_norm, meta = get_vernacular_normalizer().normalize_query(query)
        except Exception:
            v_norm = query

        lowered = v_norm.lower()
        additions = [v for k, v in QUERY_EXPANSIONS.items() if k in lowered]
        return " ".join([v_norm, *additions])

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

    # ── Stage 2: Cross-Encoder Reranking ─────────────────────────────────────────

    def _rerank(self, query: str, candidates: list[tuple[int, float]], top_k: int) -> list[tuple[int, float]]:
        """
        Rerank candidate documents using BGE-Reranker-v2-M3 cross-encoder.

        Args:
            query: The original user query string.
            candidates: List of (doc_index, stage1_score) from Stage 1.
            top_k: Number of final results to return.

        Returns:
            List of (doc_index, reranker_score) sorted by reranker relevance.
        """
        if self.reranker is None or not candidates:
            return candidates[:top_k]

        # Build (query, document_text) pairs for the cross-encoder
        pairs = []
        for doc_idx, _ in candidates:
            doc = self.documents[doc_idx]
            # Construct a rich document representation for the reranker
            doc_text = " ".join(filter(None, [
                doc.get("standard", ""),
                doc.get("title", ""),
                doc.get("category", ""),
                doc.get("text", "")[:1024],   # cap text length for efficiency
            ]))
            pairs.append((query, doc_text))

        try:
            # CrossEncoder.predict returns a list of relevance scores
            reranker_scores = self.reranker.predict(pairs, show_progress_bar=False)

            # Pair each candidate doc_index with its reranker score
            reranked = [
                (candidates[i][0], float(reranker_scores[i]))
                for i in range(len(candidates))
            ]

            # Sort by reranker score (highest = most relevant)
            reranked.sort(key=lambda x: x[1], reverse=True)

            return reranked[:top_k]

        except Exception as exc:
            print(f"[retriever] Reranking failed ({exc}) -> returning Stage 1 results")
            return candidates[:top_k]

    # ── Main retrieve (Two-Stage Pipeline) ───────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Two-stage retrieval pipeline:
          Stage 1: BM25 + BGE-M3 dense embeddings → top STAGE1_POOL_SIZE candidates
          Stage 2: BGE-Reranker-v2-M3 cross-encoder → final top_k results

        Returns the same contract as before:
            [{"standard": str, "title": str, "score": float}, ...]
        """
        expanded        = self._expanded_query(query)
        query_tokens    = tokenize(expanded)
        query_counts    = Counter(query_tokens)
        explicit_matches = self._explicit_standard_matches(query)

        # ── Stage 1: BM25 phase ─────────────────────────────────────────────────
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

        # ── Stage 1: Semantic phase (skip if unavailable) ───────────────────────
        # Determine the pool size: if reranker is available, fetch a larger pool
        pool_size = STAGE1_POOL_SIZE if self.reranker is not None else top_k

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

        # ── Stage 1 candidates (broad pool) ──────────────────────────────────────
        stage1_candidates = scored[:pool_size]

        # ── Stage 2: Cross-Encoder Reranking (precision) ─────────────────────────
        final_results = self._rerank(query, stage1_candidates, top_k)

        return [
            {
                "standard": self.documents[i]["standard"],
                "title":    self.documents[i].get("title", ""),
                "score":    score,
            }
            for i, score in final_results
        ]


# ── Singleton ────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_retriever() -> BISRetriever:
    return BISRetriever()