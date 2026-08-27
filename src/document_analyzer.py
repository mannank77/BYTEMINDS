"""
Document Analyzer — Tender Document Upload & Compliance Audit Engine
=====================================================================
Extracts text from PDF / DOCX / TXT documents, detects IS code references,
identifies product descriptions, checks currency status, and generates a
comprehensive compliance gap analysis report.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from src.currency_manager import get_currency_manager
from src.compliance_checker import get_compliance_checker
from src.normative_tracker import get_normative_tracker
from src.pipeline import run_enriched_pipeline


# ── IS Code Detection Pattern ──────────────────────────────────────────────────
# Matches patterns like: IS 269, IS 269:2015, IS 1786:2008, IS 1489 (Part 1): 1991,
# IS 2185 (Part 2), IS 456: 2000, IS:383-1970, etc.
IS_CODE_PATTERN = re.compile(
    r"\bIS\s*[:\-]?\s*(\d{2,5})"
    r"(?:\s*\(\s*(?:Part|PART)\s*(\d+)\s*\))?"
    r"(?:\s*[:\-]\s*(\d{4}))?"
    r"(?:\s*(?:Amendment|Amd\.?)\s*(?:No\.?\s*)?(\d+))?",
    re.IGNORECASE
)

# Common product/material description patterns in tender documents
PRODUCT_PATTERNS = [
    # "Supply of <product>" or "Procurement of <product>"
    re.compile(r"(?:supply|procurement|purchase|provision)\s+of\s+(.{15,120}?)(?:\.|,|\n|$)", re.IGNORECASE),
    # "conforming to IS <code>" context extraction
    re.compile(r"(.{15,100}?)\s*(?:conforming|confirming|as per|according)\s+to\s+IS", re.IGNORECASE),
    # "Material: <description>"
    re.compile(r"(?:material|product|item)\s*[:—-]\s*(.{10,120}?)(?:\.|,|\n|$)", re.IGNORECASE),
    # "Specification for <product>"
    re.compile(r"specification\s+(?:for|of)\s+(.{10,120}?)(?:\.|,|\n|$)", re.IGNORECASE),
    # "Grade <X> cement/steel/concrete"
    re.compile(r"((?:grade|fe)\s*\d+\w?\s+\w+(?:\s+\w+){0,5})", re.IGNORECASE),
]

# Section header patterns for document structure analysis
SECTION_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:(\d+(?:\.\d+)*)\s*[.\)]\s*|"
    r"(?:SECTION|CLAUSE|ITEM|SCHEDULE|PART)\s*[-:\s]*(\w+)\s*[.:\-]\s*)"
    r"(.{5,120}?)(?:\n|$)",
    re.IGNORECASE
)


@dataclass
class DetectedISCode:
    """A single IS code reference found in the document."""
    raw_match: str
    standard_id: str        # Normalized e.g. "IS 269"
    year: Optional[str]     # e.g. "2015" or None
    part: Optional[str]     # e.g. "1" or None
    amendment: Optional[str]
    line_context: str       # Surrounding text for context
    position: int           # Character offset in document
    is_current: bool = True
    current_version: str = ""
    currency_status: str = ""
    warning: str = ""


@dataclass
class DetectedProduct:
    """A product/material description extracted from the document."""
    description: str
    source_context: str
    position: int


@dataclass
class DocumentAnalysisReport:
    """Complete analysis report for an uploaded document."""
    filename: str
    total_pages: int
    total_chars: int
    total_words: int
    extraction_time: float
    detected_is_codes: List[DetectedISCode] = field(default_factory=list)
    detected_products: List[DetectedProduct] = field(default_factory=list)
    outdated_codes: List[DetectedISCode] = field(default_factory=list)
    missing_normative: List[Dict[str, Any]] = field(default_factory=list)
    recommended_standards: List[Dict[str, Any]] = field(default_factory=list)
    compliance_gaps: List[Dict[str, str]] = field(default_factory=list)
    sections_found: List[str] = field(default_factory=list)


class DocumentAnalyzer:
    """
    Analyzes uploaded tender documents for BIS standards compliance.
    Supports PDF, DOCX, and TXT formats.
    """

    def __init__(self):
        self.currency_mgr = get_currency_manager()
        self.compliance_chk = get_compliance_checker()
        self.normative_trk = get_normative_tracker()

    # ── Text Extraction ────────────────────────────────────────────────────────

    @staticmethod
    def extract_text_from_pdf(file_obj) -> Tuple[str, int]:
        """Extract text from an uploaded PDF file object. Returns (text, page_count)."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_obj)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages), len(reader.pages)
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")

    @staticmethod
    def extract_text_from_docx(file_obj) -> Tuple[str, int]:
        """Extract text from an uploaded DOCX file object."""
        try:
            import docx
            doc = docx.Document(file_obj)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs), len(paragraphs)
        except ImportError:
            # Fallback: try reading as XML
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_obj) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for para in tree.iter(f"{{{ns['w']}}}p"):
                texts = [node.text for node in para.iter(f"{{{ns['w']}}}t") if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            return "\n".join(paragraphs), len(paragraphs)
        except Exception as e:
            raise ValueError(f"Failed to read DOCX: {e}")

    @staticmethod
    def extract_text_from_txt(file_obj) -> Tuple[str, int]:
        """Extract text from an uploaded TXT file object."""
        try:
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            lines = content.split("\n")
            return content, len(lines)
        except Exception as e:
            raise ValueError(f"Failed to read TXT: {e}")

    def extract_text(self, file_obj, filename: str) -> Tuple[str, int]:
        """Auto-detect format and extract text."""
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_obj)
        elif ext in (".docx", ".doc"):
            return self.extract_text_from_docx(file_obj)
        elif ext in (".txt", ".text", ".csv"):
            return self.extract_text_from_txt(file_obj)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported: PDF, DOCX, TXT")

    # ── IS Code Detection ──────────────────────────────────────────────────────

    def detect_is_codes(self, text: str) -> List[DetectedISCode]:
        """Find all IS code references in the document text."""
        detected = []
        seen = set()

        for match in IS_CODE_PATTERN.finditer(text):
            number = match.group(1)
            part = match.group(2)
            year = match.group(3)
            amendment = match.group(4)

            # Build normalized standard ID
            std_id = f"IS {number}"
            if part:
                std_id += f" (Part {part})"

            # Skip duplicates (same standard)
            dedup_key = f"{std_id}:{year or ''}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            # Extract surrounding context (±80 chars)
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].replace("\n", " ").strip()
            context = re.sub(r"\s+", " ", context)

            # Check currency status
            currency = self.currency_mgr.get_currency_status(std_id)
            is_current = currency.get("is_current", True)
            curr_ver = currency.get("current_version", std_id)
            status = currency.get("status", "UNKNOWN")
            warning = currency.get("warning_message", "")

            # If year is specified, cross-check against current year
            if year and curr_ver and year not in curr_ver and status != "UNKNOWN":
                warning = f"Document references {std_id}: {year}, but current active version is {curr_ver}."
                is_current = False

            detected.append(DetectedISCode(
                raw_match=match.group(0),
                standard_id=std_id,
                year=year,
                part=part,
                amendment=amendment,
                line_context=context,
                position=match.start(),
                is_current=is_current,
                current_version=curr_ver,
                currency_status=status,
                warning=warning
            ))

        return detected

    # ── Product Description Extraction ─────────────────────────────────────────

    def detect_products(self, text: str) -> List[DetectedProduct]:
        """Extract product/material descriptions from the document."""
        products = []
        seen_descriptions = set()

        for pattern in PRODUCT_PATTERNS:
            for match in pattern.finditer(text):
                desc = match.group(1).strip()
                desc = re.sub(r"\s+", " ", desc)

                # Filter out too short or too generic
                if len(desc) < 12 or desc.lower() in seen_descriptions:
                    continue

                # Filter out section headers or page numbers
                if re.match(r"^\d+\s*$", desc) or desc.upper() == desc and len(desc) < 20:
                    continue

                seen_descriptions.add(desc.lower())

                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 40)
                context = text[start:end].replace("\n", " ").strip()

                products.append(DetectedProduct(
                    description=desc,
                    source_context=context,
                    position=match.start()
                ))

        return products[:15]  # Cap at 15 product descriptions

    # ── Section Structure Detection ────────────────────────────────────────────

    def detect_sections(self, text: str) -> List[str]:
        """Detect document section headers/structure."""
        sections = []
        for match in SECTION_PATTERN.finditer(text):
            num = match.group(1) or match.group(2) or ""
            title = match.group(3).strip()
            if len(title) > 5:
                sections.append(f"{num}. {title}" if num else title)
        return sections[:20]

    # ── Missing Normative Standards Detection ──────────────────────────────────

    def find_missing_normative(self, detected_codes: List[DetectedISCode]) -> List[Dict[str, Any]]:
        """
        For each detected standard, check if its mandatory normative test
        methods and allied codes are also referenced in the document.
        """
        detected_ids = {code.standard_id for code in detected_codes}
        missing = []

        for code in detected_codes:
            normative = self.normative_trk.get_normative_dependencies(code.standard_id)
            test_methods = normative.get("mandatory_test_methods", [])

            for tm in test_methods:
                tm_id = tm.get("code", "")
                # Normalize for matching
                tm_base = re.match(r"IS\s*\d+", tm_id)
                if tm_base:
                    tm_normalized = tm_base.group(0)
                    if not any(tm_normalized in did for did in detected_ids):
                        missing.append({
                            "parent_standard": code.standard_id,
                            "missing_code": tm_id,
                            "missing_title": tm.get("title", ""),
                            "type": tm.get("requirement_type", "Mandatory Test Method"),
                            "severity": "HIGH"
                        })

        # Deduplicate by missing_code
        seen = set()
        unique_missing = []
        for m in missing:
            if m["missing_code"] not in seen:
                seen.add(m["missing_code"])
                unique_missing.append(m)

        return unique_missing

    # ── Full Document Analysis ─────────────────────────────────────────────────

    def analyze_document(self, file_obj, filename: str, run_recommendations: bool = True) -> DocumentAnalysisReport:
        """
        Run complete document analysis pipeline:
        1. Extract text from document
        2. Detect all IS code references
        3. Check currency/lifecycle status of each
        4. Extract product descriptions
        5. Find missing normative references
        6. Run AI recommendations on extracted product descriptions
        7. Generate compliance gap analysis
        """
        t_start = time.perf_counter()

        # Step 1: Extract text
        text, page_count = self.extract_text(file_obj, filename)
        word_count = len(text.split())

        # Step 2: Detect IS codes
        detected_codes = self.detect_is_codes(text)

        # Step 3: Find outdated codes
        outdated = [c for c in detected_codes if not c.is_current]

        # Step 4: Extract product descriptions
        products = self.detect_products(text)

        # Step 5: Detect document sections
        sections = self.detect_sections(text)

        # Step 6: Find missing normative references
        missing_normative = self.find_missing_normative(detected_codes)

        # Step 7: Run AI recommendations on product descriptions
        recommended = []
        if run_recommendations and products:
            for prod in products[:5]:  # Limit to top 5 for speed
                try:
                    result = run_enriched_pipeline(prod.description, top_k=3, validate=False)
                    if result.get("results"):
                        recommended.append({
                            "query": prod.description,
                            "recommendations": [
                                {
                                    "standard": r["standard"],
                                    "title": r["title"],
                                    "score": r["score"],
                                    "is_mandatory": r["compliance"].get("is_mandatory", False)
                                }
                                for r in result["results"]
                            ]
                        })
                except Exception:
                    pass

        # Step 8: Generate compliance gap summary
        gaps = []
        if outdated:
            gaps.append({
                "type": "OUTDATED_STANDARDS",
                "severity": "HIGH",
                "message": f"{len(outdated)} standard(s) referenced are superseded or outdated. Using outdated standards in tender specifications may lead to procurement disputes.",
                "count": len(outdated)
            })
        if missing_normative:
            gaps.append({
                "type": "MISSING_TEST_METHODS",
                "severity": "HIGH",
                "message": f"{len(missing_normative)} mandatory test method(s) / normative reference(s) are not mentioned in the document. Omitting these may result in incomplete QA verification.",
                "count": len(missing_normative)
            })

        # Check if any detected standard has mandatory QCO but document doesn't mention ISI/certification
        text_lower = text.lower()
        for code in detected_codes:
            comp = self.compliance_chk.check_compliance(code.standard_id)
            if comp.get("is_mandatory") and "isi" not in text_lower and "certification" not in text_lower and "bis mark" not in text_lower:
                gaps.append({
                    "type": "MISSING_QCO_REQUIREMENT",
                    "severity": "CRITICAL",
                    "message": f"{code.standard_id} is under mandatory QCO (Scheme-I ISI Mark), but the document does not mention ISI certification or BIS mark requirements. This is a statutory compliance gap.",
                    "count": 1
                })
                break  # One warning is enough

        if not detected_codes and not products:
            gaps.append({
                "type": "NO_STANDARDS_FOUND",
                "severity": "INFO",
                "message": "No Indian Standard (IS) code references or product descriptions were detected in this document. Please ensure the uploaded file contains technical specifications or tender clauses.",
                "count": 0
            })

        t_elapsed = time.perf_counter() - t_start

        return DocumentAnalysisReport(
            filename=filename,
            total_pages=page_count,
            total_chars=len(text),
            total_words=word_count,
            extraction_time=t_elapsed,
            detected_is_codes=detected_codes,
            detected_products=products,
            outdated_codes=outdated,
            missing_normative=missing_normative,
            recommended_standards=recommended,
            compliance_gaps=gaps,
            sections_found=sections
        )


# ── Singleton ────────────────────────────────────────────────────────────────────
_document_analyzer: Optional[DocumentAnalyzer] = None

def get_document_analyzer() -> DocumentAnalyzer:
    global _document_analyzer
    if _document_analyzer is None:
        _document_analyzer = DocumentAnalyzer()
    return _document_analyzer
