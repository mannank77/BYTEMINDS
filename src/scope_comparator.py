"""
Scope Comparator & Disambiguation Engine
Performs side-by-side comparative differentiation between overlapping standards
(e.g., IS 456 RCC vs IS 1343 PSC, IS 269 OPC vs IS 1489 PPC vs IS 455 PSC).
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from src.currency_manager import get_currency_manager
from src.parameter_extractor import get_parameter_extractor
from src.compliance_checker import get_compliance_checker

COMPARISON_PROFILES = {
    "CEMENT": {
        "codes": ["IS 269", "IS 1489 (Part 1)", "IS 1489 (Part 2)", "IS 455", "IS 3466", "IS 6452", "IS 6909"],
        "attributes": [
          ("Primary Application", {
              "IS 269": "High early-strength structural RCC, heavy precast, multi-story frameworks.",
              "IS 1489 (Part 1)": "Mass concreting, residential plastering, general RCC, hydraulic structures.",
              "IS 1489 (Part 2)": "Structures exposed to sulphate soils and moderate chemical environments.",
              "IS 455": "Marine works, coastal foundations, wastewater sewers, and chemical plants.",
              "IS 3466": "Non-structural masonry mortars and wall plastering only (Never use in RCC).",
              "IS 6452": "Refractory construction and cold regions (sub-18°C) requiring rapid strength.",
              "IS 6909": "Extreme sulphate-bearing soil, acidic industrial effluent channels, and marine piles."
          }),
          ("Heat of Hydration", {
              "IS 269": "High — rapid temperature rise; risk of thermal cracks in thick pours.",
              "IS 1489 (Part 1)": "Low — minimal thermal cracking, highly suitable for mass gravity dams and thick rafts.",
              "IS 1489 (Part 2)": "Low to Moderate.",
              "IS 455": "Very Low — excellent temperature control during hydration.",
              "IS 3466": "Low.",
              "IS 6452": "Extremely High (requires strict temperature management).",
              "IS 6909": "Very Low."
          }),
          ("Sulphate / Chemical Resistance", {
              "IS 269": "Moderate (Vulnerable to aggressive groundwater sulphates unless special C3A limits apply).",
              "IS 1489 (Part 1)": "High (Pore refinement limits sulphate penetration).",
              "IS 1489 (Part 2)": "High.",
              "IS 455": "Very High (Dense microstructure resists chloride and sulphate ingress).",
              "IS 3466": "Low.",
              "IS 6452": "High against dilute acids, but susceptible to chemical conversion in warm humid conditions.",
              "IS 6909": "Maximum Sulphate Resistance available in Indian Standards."
          }),
          ("Curing Requirement", {
              "IS 269": "Standard (Min 7 to 10 days moist curing).",
              "IS 1489 (Part 1)": "Extended (Min 10 to 14 days moist curing due to slower pozzolanic reaction).",
              "IS 1489 (Part 2)": "Extended (Min 10 to 14 days).",
              "IS 455": "Prolonged moist curing essential for optimum slag activation.",
              "IS 3466": "Standard curing for masonry.",
              "IS 6452": "Continuous water sprinkling for first 24 hours.",
              "IS 6909": "Standard moist curing under 40°C."
          }),
          ("28-Day Strength Range", {
              "IS 269": "33 MPa, 43 MPa, or 53 MPa (Grade-specific).",
              "IS 1489 (Part 1)": "Min 33 MPa (Often matches 43/53 grade at 90 days due to secondary hydration).",
              "IS 1489 (Part 2)": "Min 33 MPa.",
              "IS 455": "Min 33 MPa.",
              "IS 3466": "Min 5.0 MPa (Masonry grade only).",
              "IS 6452": "Min 35 MPa (Rapid: reaches 30 MPa within 24 hours).",
              "IS 6909": "Min 30 MPa."
          })
        ]
    },
    "CONCRETE_DESIGN": {
        "codes": ["IS 456", "IS 1343", "IS 4926"],
        "attributes": [
          ("Structural Scope", {
              "IS 456": "Plain and Reinforced Concrete (RCC) for general buildings, foundations, and slabs.",
              "IS 1343": "Prestressed Concrete (PSC) — post-tensioned & pre-tensioned beams, long-span bridge girders.",
              "IS 4926": "Ready-Mixed Concrete (RMC) — batching, transit mixer delivery, and plant quality assurance."
          }),
          ("Minimum Concrete Grade", {
              "IS 456": "M20 for RCC; M15 for Plain Concrete (PCC).",
              "IS 1343": "M30 for Post-tensioned; M40 for Pre-tensioned prestressed members.",
              "IS 4926": "As specified by project structural engineer (typically M20 to M60+)."
          }),
          ("Primary Failure / Serviceability Focus", {
              "IS 456": "Flexure, shear, deflection control, crack width limit 0.3mm (0.2mm in severe exposure).",
              "IS 1343": "Prestress loss calculations, transfer stress checks, zero-tension / controlled cracking criteria.",
              "IS 4926": "Transit workability retention, batch uniformity, delivery temperature, 28-day cube sampling."
          })
        ]
    },
    "AGGREGATES": {
        "codes": ["IS 383", "IS 2116", "IS 9142"],
        "attributes": [
            ("Application Domain", {
                "IS 383": "Structural concrete (coarse aggregates, natural sand, M-sand, recycled aggregate).",
                "IS 2116": "Sand specifically for brick/stone masonry mortars and plastering.",
                "IS 9142": "Artificial lightweight aggregates for lightweight concrete masonry blocks."
            }),
            ("Maximum Silt / Clay Tolerance", {
                "IS 383": "Natural sand: ≤ 3.0%; Crushed Stone Sand (M-Sand): ≤ 15.0%.",
                "IS 2116": "Natural / crushed gravel sand: ≤ 5.0% by mass.",
                "IS 9142": "Clay lumps: ≤ 2.0%."
            })
        ]
    }
}


class ScopeComparator:
    def __init__(self):
        self.currency_mgr = get_currency_manager()
        self.compliance_checker = get_compliance_checker()
        self.param_extractor = get_parameter_extractor()

    def compare_standards(self, standard_ids: List[str]) -> Dict[str, Any]:
        """
        Compare a list of standard IDs and generate a structured comparison matrix.
        """
        base_codes = [self.currency_mgr.extract_base_code(s) for s in standard_ids]
        base_codes = list(dict.fromkeys(base_codes)) # preserve order & deduplicate

        if len(base_codes) < 2:
            return {
                "comparison_possible": False,
                "message": "At least two distinct standards are required for comparative differentiation."
            }

        # Check for pre-built domain comparisons
        matched_profile = None
        for prof_name, prof_data in COMPARISON_PROFILES.items():
            matched_in_prof = [c for c in base_codes if c in prof_data["codes"]]
            if len(matched_in_prof) >= 2:
                matched_profile = prof_data
                break

        attributes_matrix = []

        if matched_profile:
            for attr_name, attr_dict in matched_profile["attributes"]:
                row = {"attribute": attr_name, "values": {}}
                for code in base_codes:
                    row["values"][code] = attr_dict.get(code, "Consult standard specification clause.")
                attributes_matrix.append(row)
        else:
            # Generic automated dynamic comparison
            for code in base_codes:
                curr = self.currency_mgr.get_currency_status(code)
                comp = self.compliance_checker.check_compliance(code)
                # Build rows
                pass

        # Meta overview per standard
        standards_meta = {}
        for code in base_codes:
            curr = self.currency_mgr.get_currency_status(code)
            comp = self.compliance_checker.check_compliance(code)
            standards_meta[code] = {
                "title": curr.get("title", code),
                "current_version": curr.get("current_version", code),
                "status": curr.get("status", "ACTIVE"),
                "is_mandatory_qco": comp.get("is_mandatory", False),
                "scheme": comp.get("certification_scheme", "")
            }

        return {
            "comparison_possible": True,
            "compared_standards": base_codes,
            "standards_meta": standards_meta,
            "matrix": attributes_matrix,
            "selection_guide": self._generate_selection_guide(base_codes)
        }

    def _generate_selection_guide(self, base_codes: List[str]) -> str:
        if "IS 456" in base_codes and "IS 1343" in base_codes:
            return "💡 Decision Rule: Use IS 456 for standard RCC buildings/foundations. Switch to IS 1343 when using post-tensioned tendons or pre-tensioned long-span infrastructure girders."
        if "IS 269" in base_codes and "IS 1489 (Part 1)" in base_codes:
            return "💡 Decision Rule: Use IS 269 (OPC) when rapid formwork removal and early strength is required. Choose IS 1489 (PPC) for residential construction, plastering, mass concrete, and when higher resistance to chemical leaching is desired."
        if "IS 455" in base_codes:
            return "💡 Decision Rule: Select IS 455 (PSC) for marine, coastal, port, or high-sulphate sewage environments due to superior slag density."
        return "💡 Decision Rule: Verify project structural drawings and environmental exposure conditions before finalizing standard choice."


# Global singleton
_scope_comparator: Optional[ScopeComparator] = None

def get_scope_comparator() -> ScopeComparator:
    global _scope_comparator
    if _scope_comparator is None:
        _scope_comparator = ScopeComparator()
    return _scope_comparator
