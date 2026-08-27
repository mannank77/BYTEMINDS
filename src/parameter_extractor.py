"""
Technical Parameter Extractor
Extracts and structures quantitative technical parameters, physical criteria,
and chemical limit clauses for standard specifications.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

PARAMS_DB_PATH = Path("data/parameters_db.json")


class ParameterExtractor:
    def __init__(self, db_file: Path | str = PARAMS_DB_PATH):
        self.db_file = Path(db_file)
        self.db: Dict[str, Any] = {}
        self._load_db()

    def _load_db(self) -> None:
        if self.db_file.exists():
            with open(self.db_file, "r", encoding="utf-8") as f:
                self.db = json.load(f)
        else:
            self.db = {}

    def extract_base_code(self, standard_id: str) -> str:
        clean = standard_id.strip()
        part_match = re.match(r"(IS\s*\d+\s*(?:\([^)]+\))?)", clean, re.IGNORECASE)
        if part_match:
            return re.sub(r"\s+", " ", part_match.group(1)).strip()
        return clean.split(":")[0].strip()

    def get_technical_parameters(self, standard_id: str) -> Dict[str, Any]:
        base_code = self.extract_base_code(standard_id)
        data = self.db.get(base_code)

        if not data:
            for key, val in self.db.items():
                if key.lower() in standard_id.lower() or standard_id.lower() in key.lower():
                    data = val
                    base_code = key
                    break

        if not data:
            return {
                "base_code": base_code,
                "has_parameters": False,
                "parameters": {}
            }

        return {
            "base_code": base_code,
            "has_parameters": True,
            "standard": data.get("standard", standard_id),
            "parameters": data
        }


# Global singleton
_parameter_extractor: Optional[ParameterExtractor] = None

def get_parameter_extractor() -> ParameterExtractor:
    global _parameter_extractor
    if _parameter_extractor is None:
        _parameter_extractor = ParameterExtractor()
    return _parameter_extractor
