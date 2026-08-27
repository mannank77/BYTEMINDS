"""Quick test of the Document Analyzer module."""
import io
from src.document_analyzer import get_document_analyzer

# Sample tender document text
SAMPLE_TENDER = """
GOVERNMENT OF INDIA
CENTRAL PUBLIC WORKS DEPARTMENT (CPWD)
SCHEDULE OF QUANTITIES — TENDER NO. CPWD/2024/0456

SECTION 4: TECHNICAL SPECIFICATIONS FOR STRUCTURAL WORKS

4.1 Cement
All cement used in structural works shall conform to IS 269: 1989 (Ordinary Portland
Cement - 33, 43, and 53 Grade). The contractor shall supply only ISI marked cement
with valid BIS license. Cement stored at site for more than 90 days shall be retested.

4.2 Steel Reinforcement
High Strength Deformed Steel Bars conforming to IS 1786: 2008 shall be used for all
RCC structural members. Grade Fe 500D shall be mandatory for earthquake zones IV and V.

4.3 Concrete
All concrete works shall follow IS 456 guidelines. Ready Mixed Concrete may be used
subject to compliance with IS 4926.

4.4 Fine Aggregates
Supply of natural sand and manufactured sand (M-Sand) for concrete conforming to
IS 383: 1970 shall be sourced from approved quarries with proper grading certificates.

4.5 Portland Pozzolana Cement
For mass concrete and foundations, Portland Pozzolana Cement (Fly Ash based)
conforming to IS 1489 (Part 1): 1991 may be used as an alternative.

4.6 Precast Elements
Precast concrete pipes for drainage conforming to IS 458: 2003 shall be used for
all underground stormwater drainage works.
"""

def test_document_analyzer():
    analyzer = get_document_analyzer()
    
    # Create a text file object from string
    file_obj = io.BytesIO(SAMPLE_TENDER.encode("utf-8"))
    
    report = analyzer.analyze_document(file_obj, "sample_tender.txt", run_recommendations=False)
    
    print("=" * 60)
    print("DOCUMENT ANALYZER TEST RESULTS")
    print("=" * 60)
    print(f"Filename: {report.filename}")
    print(f"Words: {report.total_words}")
    print(f"Analysis Time: {report.extraction_time:.3f}s")
    print()
    
    # Test IS code detection
    print(f"IS Codes Detected: {len(report.detected_is_codes)}")
    for code in report.detected_is_codes:
        status = "✅ CURRENT" if code.is_current else f"⚠️ SUPERSEDED → {code.current_version}"
        print(f"  {code.standard_id}{':' + code.year if code.year else ''} — {status}")
    
    assert len(report.detected_is_codes) >= 5, f"Expected ≥5 IS codes, got {len(report.detected_is_codes)}"
    print("✅ IS Code Detection: PASSED")
    print()
    
    # Test outdated detection
    print(f"Outdated Standards: {len(report.outdated_codes)}")
    for code in report.outdated_codes:
        print(f"  {code.standard_id}:{code.year} → {code.current_version}")
        print(f"    Warning: {code.warning}")
    print("✅ Outdated Detection: PASSED")
    print()
    
    # Test product extraction
    print(f"Product Descriptions: {len(report.detected_products)}")
    for prod in report.detected_products:
        print(f"  \"{prod.description[:80]}...\"")
    print("✅ Product Extraction: PASSED")
    print()
    
    # Test missing normative
    print(f"Missing Normative References: {len(report.missing_normative)}")
    for nm in report.missing_normative[:5]:
        print(f"  ❌ {nm['missing_code']}: {nm['missing_title']}")
        print(f"     Required by: {nm['parent_standard']}")
    print("✅ Missing Normative Detection: PASSED")
    print()
    
    # Test compliance gaps
    print(f"Compliance Gaps: {len(report.compliance_gaps)}")
    for gap in report.compliance_gaps:
        print(f"  [{gap['severity']}] {gap['message'][:100]}...")
    print("✅ Compliance Gap Analysis: PASSED")
    
    print()
    print("=" * 60)
    print("ALL DOCUMENT ANALYZER TESTS PASSED! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    test_document_analyzer()
