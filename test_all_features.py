import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.currency_manager import get_currency_manager
from src.normative_tracker import get_normative_tracker
from src.parameter_extractor import get_parameter_extractor
from src.compliance_checker import get_compliance_checker
from src.vernacular_normalizer import get_vernacular_normalizer
from src.scope_comparator import get_scope_comparator
from src.tender_generator import get_tender_generator
from src.pipeline import run_enriched_pipeline, run_pipeline


def test_currency_manager():
    mgr = get_currency_manager()
    res = mgr.get_currency_status("IS 269: 1989")
    assert res["is_current"] is False, "IS 269: 1989 must be detected as SUPERSEDED"
    assert "IS 269: 2015" in res["current_version"]
    assert res["warning_message"] is not None
    print("✅ 1. Version Currency & Revision Tracking: PASSED")


def test_normative_tracker():
    trk = get_normative_tracker()
    res = trk.get_normative_dependencies("IS 269")
    codes = [tm["code"] for tm in res["mandatory_test_methods"]]
    assert any("4031" in c for c in codes), "Must include IS 4031 physical tests"
    assert any("4032" in c for c in codes), "Must include IS 4032 chemical tests"
    print("✅ 2. Normative Dependency Graph & Testing Standards: PASSED")


def test_parameter_extractor():
    ext = get_parameter_extractor()
    res = ext.get_technical_parameters("IS 269")
    assert res["has_parameters"] is True
    assert "fineness_blaine_min_m2_kg" in res["parameters"]["physical_requirements"]
    print("✅ 3. Structured Technical Parameter Extraction: PASSED")


def test_compliance_checker():
    chk = get_compliance_checker()
    res = chk.check_compliance("IS 269")
    assert res["is_mandatory"] is True, "Cement must be mandatory under QCO"
    assert "ISI" in res["certification_scheme"]
    assert "Section 16" in res["statutory_provisions"]
    print("✅ 4. QCO & Regulatory Compliance Layer: PASSED")


def test_vernacular_normalizer():
    norm = get_vernacular_normalizer()
    text, meta = norm.normalize_query("मुझे छत की सीमेंट और 16mm सरिया चाहिए")
    assert meta["is_vernacular"] is True
    assert "1786" in text or "TMT" in text
    assert "cement" in text.lower() or "456" in text
    print("✅ 5. Vernacular / Multilingual (Hindi & Hinglish) Processing: PASSED")


def test_scope_comparator():
    comp = get_scope_comparator()
    res = comp.compare_standards(["IS 456", "IS 1343"])
    assert res["comparison_possible"] is True
    assert len(res["matrix"]) > 0
    print("✅ 6. Scope Disambiguation & Comparative Matrix: PASSED")


def test_tender_generator():
    gen = get_tender_generator()
    res = gen.generate_tender_clause("IS 269")
    assert "SPECIFICATION CLAUSE" in res["tender_clause_markdown"]
    assert len(res["qa_checklist"]) >= 4
    print("✅ 7. Tender Clause & Site QA Checklist Generator: PASSED")


def test_enriched_pipeline():
    enriched = run_enriched_pipeline("Ordinary Portland cement 53 grade", top_k=3)
    assert enriched["is_valid"] is True
    assert len(enriched["results"]) > 0
    first = enriched["results"][0]
    assert "currency" in first
    assert "normative" in first
    assert "compliance" in first
    print("✅ 8. End-to-End Enriched Pipeline: PASSED")


if __name__ == "__main__":
    print("=" * 50)
    print("RUNNING BIS ENGINE CAPABILITY SUITE (BYTEMINDS)")
    print("=" * 50)
    test_currency_manager()
    test_normative_tracker()
    test_parameter_extractor()
    test_compliance_checker()
    test_vernacular_normalizer()
    test_scope_comparator()
    test_tender_generator()
    test_enriched_pipeline()
    print("=" * 50)
    print("ALL 8 VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")
    print("=" * 50)
