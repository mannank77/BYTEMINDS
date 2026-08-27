"""
Normative & Allied Reference Dependency Tracker
Resolves testing standards (e.g. IS 4031, IS 4032, IS 2386), codes of practice,
and material feedstock dependencies for primary BIS standards.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

GRAPH_PATH = Path("data/normative_graph.json")


class NormativeTracker:
    def __init__(self, graph_file: Path | str = GRAPH_PATH):
        self.graph_file = Path(graph_file)
        self.graph: Dict[str, Any] = {}
        self._load_graph()

    def _load_graph(self) -> None:
        if self.graph_file.exists():
            with open(self.graph_file, "r", encoding="utf-8") as f:
                self.graph = json.load(f)
        else:
            self.graph = {}

    def extract_base_code(self, standard_id: str) -> str:
        clean = standard_id.strip()
        part_match = re.match(r"(IS\s*\d+\s*(?:\([^)]+\))?)", clean, re.IGNORECASE)
        if part_match:
            return re.sub(r"\s+", " ", part_match.group(1)).strip()
        return clean.split(":")[0].strip()

    def get_normative_dependencies(self, standard_id: str) -> Dict[str, Any]:
        """
        Retrieve mandatory test methods, allied practice codes, and feedstock requirements.
        """
        base_code = self.extract_base_code(standard_id)
        data = self.graph.get(base_code)

        if not data:
            for key, val in self.graph.items():
                if key.lower() in standard_id.lower() or standard_id.lower() in key.lower():
                    data = val
                    base_code = key
                    break

        if not data:
            return {
                "base_code": base_code,
                "primary_standard": standard_id,
                "mandatory_test_methods": [],
                "allied_codes_of_practice": [],
                "feedstock_and_testing_sand": []
            }

        return {
            "base_code": base_code,
            "primary_standard": data.get("primary_standard", standard_id),
            "title": data.get("title", ""),
            "mandatory_test_methods": data.get("mandatory_test_methods", []),
            "allied_codes_of_practice": data.get("allied_codes_of_practice", []),
            "feedstock_and_testing_sand": data.get("feedstock_and_testing_sand", [])
        }


# Global singleton
_normative_tracker: Optional[NormativeTracker] = None

def get_normative_tracker() -> NormativeTracker:
    global _normative_tracker
    if _normative_tracker is None:
        _normative_tracker = NormativeTracker()
    return _normative_tracker
