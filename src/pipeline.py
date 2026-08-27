"""
Master Recommendation Pipeline Orchestrator
Integrates Hybrid Retrieval, LLM Guardrail Validation, Multilingual Normalization,
Version Lifecycle Tracking, Normative Dependency Graph, Technical Parameter Extraction,
QCO Regulatory Compliance, and Tender Clause Generation.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from src.retriever import get_retriever
from src.llm_classifier import validate_query
from src.currency_manager import get_currency_manager
from src.normative_tracker import get_normative_tracker
from src.parameter_extractor import get_parameter_extractor
from src.compliance_checker import get_compliance_checker
from src.vernacular_normalizer import get_vernacular_normalizer
from src.tender_generator import get_tender_generator
from src.scope_comparator import get_scope_comparator


def run_pipeline(query: str, top_k: int = 5, include_rationale: bool = False, validate: bool = True):
    """
    Return the top BIS standard identifiers for a product description.
    Preserves full backward compatibility with evaluation scripts and CLI inference.
    
    Args:
        query (str): Product description
        top_k (int): Number of standards to return
        include_rationale (bool): Include title/rationale
        validate (bool): Use LLM to validate if query is building-material related
        
    Returns:
        list: Standard identifiers or rationale dicts, or empty list if invalid.
    """
    if validate:
        validation = validate_query(query)
        if not validation["is_valid"]:
            return []
    
    hits = get_retriever().retrieve(query, top_k=top_k)
    if include_rationale:
        return [
            {
                "standard": hit["standard"],
                "rationale": f"Matched against: {hit['title']}",
            }
            for hit in hits
        ]
    return [hit["standard"] for hit in hits]


def run_enriched_pipeline(query: str, top_k: int = 5, validate: bool = False) -> Dict[str, Any]:
    """
    Execute full multi-dimensional recommendation workflow with complete metadata:
    - Vernacular query analysis
    - Hybrid retrieval scores
    - Version currency & status (Active vs Superseded)
    - Normative allied test standards
    - Structured technical parameters
    - QCO compliance & statutory mandates
    - Pre-generated tender specification clause
    """
    normalizer = get_vernacular_normalizer()
    _, vern_meta = normalizer.normalize_query(query)

    validation_result = {"is_valid": True, "reason": "Validation skipped or passed"}
    if validate:
        validation_result = validate_query(query)
        if not validation_result["is_valid"]:
            return {
                "query": query,
                "is_valid": False,
                "validation": validation_result,
                "vernacular_meta": vern_meta,
                "results": []
            }

    hits = get_retriever().retrieve(query, top_k=top_k)

    currency_mgr = get_currency_manager()
    normative_trk = get_normative_tracker()
    param_ext = get_parameter_extractor()
    compliance_chk = get_compliance_checker()
    tender_gen = get_tender_generator()

    enriched_results = []
    retrieved_codes = []

    for hit in hits:
        raw_std = hit["standard"]
        title = hit.get("title", "")
        score = hit.get("score", 0.0)

        # 1. Currency & Revisions
        currency = currency_mgr.get_currency_status(raw_std)
        base_code = currency.get("base_code", raw_std)
        retrieved_codes.append(base_code)

        # 2. Normative Dependencies
        normative = normative_trk.get_normative_dependencies(base_code)

        # 3. Technical Parameters
        params = param_ext.get_technical_parameters(base_code)

        # 4. Compliance & QCO
        compliance = compliance_chk.check_compliance(base_code)

        # 5. Tender Clause
        tender = tender_gen.generate_tender_clause(base_code)

        enriched_results.append({
            "standard": raw_std,
            "base_code": base_code,
            "title": title,
            "score": round(float(score), 4),
            "currency": currency,
            "normative": normative,
            "parameters": params,
            "compliance": compliance,
            "tender": tender
        })

    # 6. Comparative matrix for top results if >= 2 standards
    comparator = get_scope_comparator()
    comparison_matrix = comparator.compare_standards(retrieved_codes[:3])

    return {
        "query": query,
        "is_valid": True,
        "validation": validation_result,
        "vernacular_meta": vern_meta,
        "results": enriched_results,
        "comparison_matrix": comparison_matrix
    }


def get_query_validation(query: str) -> Dict[str, Any]:
    """Get validation result without running full pipeline."""
    return validate_query(query)
