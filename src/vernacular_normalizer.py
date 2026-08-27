"""
Vernacular & Multilingual Query Normalizer
Detects Hindi (Devanagari), Hinglish, and regional vernacular keywords,
translates them to standardized technical terminology, and enriches search queries.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

LEXICON_PATH = Path("data/vernacular_lexicon.json")


class VernacularNormalizer:
    def __init__(self, lexicon_file: Path | str = LEXICON_PATH):
        self.lexicon_file = Path(lexicon_file)
        self.exact_mappings: Dict[str, str] = {}
        self.keywords: Dict[str, str] = {}
        self._load_lexicon()

    def _load_lexicon(self) -> None:
        if self.lexicon_file.exists():
            with open(self.lexicon_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.exact_mappings = data.get("exact_mappings", {})
                self.keywords = data.get("vernacular_keywords", {})
        else:
            self.exact_mappings = {}
            self.keywords = {}

    def is_devanagari(self, text: str) -> bool:
        """Check if query contains Devanagari / Hindi unicode characters."""
        return bool(re.search(r"[\u0900-\u097F]", text))

    def normalize_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize query, expand vernacular terms, and return detection metadata.
        """
        raw_query = query.strip()
        lower_query = raw_query.lower()
        has_devanagari = self.is_devanagari(raw_query)

        detected_terms = []
        expanded_parts = [raw_query]

        # 1. Exact match check
        for vern_key, eng_expansion in self.exact_mappings.items():
            pattern = rf"\b{re.escape(vern_key.lower())}\b" if not self.is_devanagari(vern_key) else re.escape(vern_key)
            if re.search(pattern, lower_query if not self.is_devanagari(vern_key) else raw_query, re.IGNORECASE):
                detected_terms.append(vern_key)
                expanded_parts.append(eng_expansion)

        # 2. Keyword fallback check
        for k_word, k_trans in self.keywords.items():
            if k_word in raw_query and k_word not in detected_terms:
                detected_terms.append(k_word)
                expanded_parts.append(k_trans)

        is_vernacular = len(detected_terms) > 0 or has_devanagari
        normalized_query = " ".join(expanded_parts)

        meta = {
            "original_query": raw_query,
            "is_vernacular": is_vernacular,
            "has_devanagari": has_devanagari,
            "detected_vernacular_terms": detected_terms,
            "expanded_query": normalized_query
        }

        return normalized_query, meta


# Global singleton
_vernacular_normalizer: Optional[VernacularNormalizer] = None

def get_vernacular_normalizer() -> VernacularNormalizer:
    global _vernacular_normalizer
    if _vernacular_normalizer is None:
        _vernacular_normalizer = VernacularNormalizer()
    return _vernacular_normalizer
