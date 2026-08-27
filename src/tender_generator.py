"""
Tender Specification & QA Checklist Generator
Generates contract-ready technical specification clauses and actionable Quality Assurance
verification checklists for public works tenders (CPWD, PWD, PSUs, NHAI, Metro Rail).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from src.currency_manager import get_currency_manager
from src.compliance_checker import get_compliance_checker
from src.normative_tracker import get_normative_tracker
from src.parameter_extractor import get_parameter_extractor


class TenderGenerator:
    def __init__(self):
        self.currency_mgr = get_currency_manager()
        self.compliance_checker = get_compliance_checker()
        self.normative_tracker = get_normative_tracker()
        self.param_extractor = get_parameter_extractor()

    def generate_tender_clause(self, standard_id: str, custom_scope: str = "") -> Dict[str, Any]:
        """
        Generate legally sound tender specification clause and site inspection checklist.
        """
        base_code = self.currency_mgr.extract_base_code(standard_id)
        currency = self.currency_mgr.get_currency_status(base_code)
        compliance = self.compliance_checker.check_compliance(base_code)
        normative = self.normative_tracker.get_normative_dependencies(base_code)
        params = self.param_extractor.get_technical_parameters(base_code)

        curr_ver = currency.get("current_version", standard_id)
        title = currency.get("title", standard_id)

        # 1. Generate Tender Specification Clause
        clause_lines = []
        clause_lines.append(f"### SECTION XX: TECHNICAL SPECIFICATION CLAUSE FOR {base_code.upper()}")
        clause_lines.append(f"**Item Description:** Supply, delivery, and testing of {title}")
        clause_lines.append("")
        clause_lines.append(f"1. **Conformity to Standards:**")
        clause_lines.append(
            f"   The material supplied under this contract shall conform strictly to the latest revision "
            f"   **{curr_ver}** (including all active amendments issued by the Bureau of Indian Standards)."
        )

        if compliance.get("is_mandatory", False):
            clause_lines.append(
                f"   Under the **{compliance.get('qco_name')}** notified by the {compliance.get('issuing_ministry')}, "
                f"   the product MUST possess a valid BIS Standard Mark (**ISI Mark License**). "
                f"   Supplies without a valid ISI mark on the packaging or manufacturer test certificate (MTC) "
                f"   shall be summarily rejected at the contractor's sole risk and expense."
            )

        # Normative Testing references
        test_methods = normative.get("mandatory_test_methods", [])
        if test_methods:
            clause_lines.append("")
            clause_lines.append("2. **Mandatory Testing & Quality Protocols:**")
            clause_lines.append("   All routine acceptance and compliance testing shall follow:")
            for tm in test_methods[:4]:
                clause_lines.append(f"   - **{tm['code']}**: {tm['title']} ({tm.get('requirement_type', 'Mandatory')})")

        # Technical criteria
        clause_lines.append("")
        clause_lines.append("3. **Manufacturer Test Certificates (MTC) & Batch Sampling:**")
        clause_lines.append(
            "   - Every consignment delivered to site shall be accompanied by an authentic Manufacturer Test Certificate (MTC).\n"
            "   - Random field sampling shall be conducted by the Engineer-in-Charge and tested at a NABL-accredited laboratory.\n"
            "   - Materials stored at site for more than 90 days must be re-tested for strength and soundness before use in structural works."
        )

        tender_clause_text = "\n".join(clause_lines)

        # 2. Generate QA & Site Inspection Checklist
        checklist_items = [
            {"step": "1. ISI License Verification", "action": f"Verify valid BIS Standard Mark & CM/L License number on packaging as per {curr_ver}."},
            {"step": "2. Manufacturer Test Certificate (MTC)", "action": "Cross-check batch number, date of manufacture, and MTC test values against standard limits."},
            {"step": "3. Delivery & Age Verification", "action": "Ensure cement/rebar delivered is within acceptable shelf-life (re-test required if > 90 days from manufacture)."},
            {"step": "4. Field Sampling", "action": f"Extract random representative samples for testing in accordance with {test_methods[0]['code'] if test_methods else 'relevant IS test code'}."},
            {"step": "5. Mandatory Testing Verification", "action": "Ensure 3-day, 7-day, and 28-day strength and soundness test reports satisfy technical parameters before casting."}
        ]

        return {
            "standard_id": base_code,
            "current_version": curr_ver,
            "title": title,
            "is_mandatory": compliance.get("is_mandatory", False),
            "tender_clause_markdown": tender_clause_text,
            "qa_checklist": checklist_items
        }


# Global singleton
_tender_generator: Optional[TenderGenerator] = None

def get_tender_generator() -> TenderGenerator:
    global _tender_generator
    if _tender_generator is None:
        _tender_generator = TenderGenerator()
    return _tender_generator
