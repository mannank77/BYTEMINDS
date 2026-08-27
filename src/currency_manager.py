"""
Version Control & Currency Manager
Tracks lifecycle states (ACTIVE, SUPERSEDED, WITHDRAWN), modern revisions,
amendments, and generates migration warnings for historical standards.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

REGISTRY_PATH = Path("data/standards_registry.json")


class CurrencyManager:
    def __init__(self, registry_file: Path | str = REGISTRY_PATH):
        self.registry_file = Path(registry_file)
        self.registry: Dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if self.registry_file.exists():
            with open(self.registry_file, "r", encoding="utf-8") as f:
                self.registry = json.load(f)
        else:
            self.registry = {}

    def extract_base_code(self, standard_id: str) -> str:
        """
        Extract base standard code from raw strings like 'IS 269: 1989' or 'IS 1489 (Part 1): 1991'.
        """
        clean = standard_id.strip()
        # Handle parts like IS 1489 (Part 1): 1991
        part_match = re.match(r"(IS\s*\d+\s*(?:\([^)]+\))?)", clean, re.IGNORECASE)
        if part_match:
            # Standardize spacing e.g., IS  269 -> IS 269
            base = re.sub(r"\s+", " ", part_match.group(1)).strip()
            return base
        return clean.split(":")[0].strip()

    def get_currency_status(self, standard_id: str) -> Dict[str, Any]:
        """
        Assess whether a standard is ACTIVE or SUPERSEDED and return full revision metadata.
        """
        base_code = self.extract_base_code(standard_id)
        info = self.registry.get(base_code)

        if not info:
            # Check for part variants or fuzzy matches
            for key, val in self.registry.items():
                if key.lower() in standard_id.lower() or standard_id.lower() in key.lower():
                    info = val
                    base_code = key
                    break

        if not info:
            return {
                "base_code": base_code,
                "current_version": standard_id,
                "status": "ACTIVE (Assumed)",
                "is_current": True,
                "warning_message": None,
                "historical_versions": [],
                "consolidation_summary": "Standard listed in active repository without documented supersession.",
                "latest_amendments": []
            }

        # Check if the specific query standard_id contains an older year than current_version
        is_superseded = False
        superseded_warning = None

        # Extract year if present
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", standard_id)
        current_year_match = re.search(r"\b(20\d\d)\b", info.get("current_version", ""))

        if year_match and current_year_match:
            query_year = int(year_match.group(1))
            current_year = int(current_year_match.group(1))
            if query_year < current_year:
                is_superseded = True
                superseded_warning = (
                    f"⚠️ Outdated Reference: '{standard_id}' has been SUPERSEDED by '{info.get('current_version')}'. "
                    f"Always reference the current active revision in project contracts."
                )

        return {
            "base_code": base_code,
            "title": info.get("title", ""),
            "current_version": info.get("current_version", standard_id),
            "status": "SUPERSEDED" if is_superseded else info.get("status", "ACTIVE"),
            "is_current": not is_superseded,
            "warning_message": superseded_warning,
            "historical_versions": info.get("historical_versions", []),
            "consolidation_summary": info.get("consolidation_summary", ""),
            "latest_amendments": info.get("latest_amendments", [])
        }


# Global singleton instance
_currency_manager: Optional[CurrencyManager] = None

def get_currency_manager() -> CurrencyManager:
    global _currency_manager
    if _currency_manager is None:
        _currency_manager = CurrencyManager()
    return _currency_manager
