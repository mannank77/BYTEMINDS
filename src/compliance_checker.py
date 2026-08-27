"""
QCO & Statutory Compliance Inspector
Analyzes mandatory Quality Control Orders (QCOs), Scheme-I ISI mark status,
issuing ministries, and legal penalties under the Bureau of Indian Standards Act, 2016.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

QCO_PATH = Path("data/qco_compliance.json")


class ComplianceChecker:
    def __init__(self, qco_file: Path | str = QCO_PATH):
        self.qco_file = Path(qco_file)
        self.qco_db: Dict[str, Any] = {}
        self._load_qco_db()

    def _load_qco_db(self) -> None:
        if self.qco_file.exists():
            with open(self.qco_file, "r", encoding="utf-8") as f:
                self.qco_db = json.load(f)
        else:
            self.qco_db = {}

    def extract_base_code(self, standard_id: str) -> str:
        clean = standard_id.strip()
        part_match = re.match(r"(IS\s*\d+\s*(?:\([^)]+\))?)", clean, re.IGNORECASE)
        if part_match:
            return re.sub(r"\s+", " ", part_match.group(1)).strip()
        return clean.split(":")[0].strip()

    def check_compliance(self, standard_id: str) -> Dict[str, Any]:
        base_code = self.extract_base_code(standard_id)
        data = self.qco_db.get(base_code)

        if not data:
            for key, val in self.qco_db.items():
                if key.lower() in standard_id.lower() or standard_id.lower() in key.lower():
                    data = val
                    base_code = key
                    break

        if not data:
            return {
                "base_code": base_code,
                "is_mandatory": False,
                "certification_scheme": "Voluntary / Standard Specification",
                "qco_name": "N/A",
                "issuing_ministry": "Bureau of Indian Standards",
                "legal_status": "VOLUNTARY STANDARD",
                "gazette_order_reference": "N/A",
                "statutory_provisions": "BIS Act 2016 general provisions.",
                "penalties_and_consequences": "Standard testing compliance for contractual acceptance.",
                "badge": "ℹ️ VOLUNTARY STANDARD"
            }

        is_mand = data.get("is_mandatory", False)
        badge = "🛑 MANDATORY UNDER QCO (ISI MARK COMPULSORY)" if is_mand else "📋 STATUTORY CODE / CONTRACTUAL MANDATE"

        return {
            "base_code": base_code,
            "is_mandatory": is_mand,
            "certification_scheme": data.get("certification_scheme", ""),
            "qco_name": data.get("qco_name", ""),
            "issuing_ministry": data.get("issuing_ministry", ""),
            "legal_status": data.get("legal_status", ""),
            "gazette_order_reference": data.get("gazette_order_reference", ""),
            "statutory_provisions": data.get("statutory_provisions", ""),
            "penalties_and_consequences": data.get("penalties_and_consequences", ""),
            "badge": badge
        }


# Global singleton
_compliance_checker: Optional[ComplianceChecker] = None

def get_compliance_checker() -> ComplianceChecker:
    global _compliance_checker
    if _compliance_checker is None:
        _compliance_checker = ComplianceChecker()
    return _compliance_checker
