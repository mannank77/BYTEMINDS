import time
import streamlit as st
import json
from src.retriever import get_retriever
from src.pipeline import run_enriched_pipeline, get_query_validation
from src.currency_manager import get_currency_manager
from src.scope_comparator import get_scope_comparator
from src.compliance_checker import get_compliance_checker

st.set_page_config(
    page_title="BIS Standards Recommendation & Compliance Engine — Team BYTEMINDS",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize singletons in cache
@st.cache_resource
def load_engine():
    return {
        "retriever": get_retriever(),
        "currency_mgr": get_currency_manager(),
        "comparator": get_scope_comparator(),
        "compliance_chk": get_compliance_checker()
    }

engine = load_engine()
retriever = engine["retriever"]
currency_mgr = engine["currency_mgr"]
comparator = engine["comparator"]
compliance_chk = engine["compliance_chk"]

# Enhanced CSS Styling
st.markdown("""
    <style>
    .main-container { max-width: 1300px; margin: 0 auto; }
    .header-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #0d47a1;
        margin: 0.5rem 0 0.2rem 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 1.05rem;
        color: #444;
        margin-bottom: 1.5rem;
    }
    .team-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .search-box {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .result-card {
        background: white;
        border: 1px solid #e0e6ed;
        border-left: 6px solid #1e3c72;
        padding: 1.25rem;
        margin: 1.2rem 0;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06);
    }
    .rank-pill {
        background: #1e3c72;
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
    .standard-code {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0d47a1;
        font-family: monospace;
    }
    .badge-active {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #c3e6cb;
        margin-left: 0.5rem;
    }
    .badge-superseded {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #ffeeba;
        margin-left: 0.5rem;
    }
    .badge-qco-mandatory {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #f5c6cb;
        margin-left: 0.5rem;
    }
    .badge-vernacular {
        background-color: #e2e3e5;
        color: #383d41;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .metric-box {
        background: #f8fafd;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
    .metric-num {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e3c72;
    }
    .metric-txt {
        font-size: 0.8rem;
        color: #64748b;
        font-weight: 600;
    }
    .alert-superseded {
        background: #fff8e6;
        border-left: 4px solid #f59e0b;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin: 0.7rem 0;
        font-size: 0.9rem;
        color: #92400e;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<div class="team-badge">✨ Developed by Team BYTEMINDS</div>', unsafe_allow_html=True)
st.markdown('<div class="header-title">🏗️ BIS Standards Recommendation & Compliance Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Intelligent Hybrid Retrieval, Normative Dependency Graph, Technical Parameter Extraction, QCO Compliance & Tender Generator</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Search & Filter Settings")
    enable_validation = st.checkbox("🤖 Enable Local LLM Guardrail", value=False, help="Use Ollama (phi:2.7b) to filter out non-construction queries")
    top_k = st.slider("📊 Recommendations (Top-K)", min_value=3, max_value=8, value=5)
    
    st.divider()
    st.subheader("📚 Quick Vernacular Tests")
    st.caption("Click to test multilingual & regional queries:")
    
    quick_queries = [
        "सरिया 16mm Fe 500D (TMT Rebar)",
        "छत की सीमेंट (Roof Slab Concrete)",
        "बालू और कंक्रीट रेत (Fine Aggregates)",
        "Ordinary Portland Cement 53 Grade",
        "Prestressed Concrete Bridge Girders",
        "Ready-Mixed Concrete Batching Plant"
    ]
    
    selected_quick = None
    for q in quick_queries:
        if st.button(f"👉 {q}", use_container_width=True):
            st.session_state["query_input"] = q
            st.rerun()
            
    st.divider()
    st.markdown("""
    **Engine Capabilities:**
    - ✅ **Hybrid BM25 + Semantic Search**
    - ✅ **Lifecycle & Revision Tracking**
    - ✅ **Normative Test Standards (IS 4031/32)**
    - ✅ **QCO & Mandatory ISI Schemes**
    - ✅ **Indic & Vernacular Processing**
    - ✅ **Tender Specification Clauses**
    """)

# Top Level Tabs
tab_search, tab_compare, tab_registry, tab_credits = st.tabs([
    "🔍 Smart Search & Complete Specification",
    "🔄 Side-by-Side Scope Comparator",
    "📜 Standards & QCO Registry Browser",
    "👥 Team BYTEMINDS"
])

# ── TAB 1: Smart Search & Complete Specification ────────────────────────────────
with tab_search:
    default_text = st.session_state.get("query_input", "")
    
    with st.form("search_form"):
        st.markdown("##### 📝 Enter Material or Product Query (English / Hindi / Hinglish)")
        query = st.text_area(
            "Query Description",
            value=default_text,
            height=90,
            placeholder="e.g. High-strength OPC 53 grade cement for structural columns OR सरिया Fe 500D earthquake resistant rebar OR छत की सीमेंट...",
            label_visibility="collapsed"
        )
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submitted = st.form_submit_button("🔍 Find Standards & Complete Specs", use_container_width=True, type="primary")
        with col2:
            clear_btn = st.form_submit_button("🗑️ Clear Search", use_container_width=True)
            
    if clear_btn:
        st.session_state["query_input"] = ""
        st.rerun()

    if submitted or (default_text and not clear_btn):
        active_q = query.strip() if query else default_text.strip()
        if len(active_q) < 3:
            st.warning("⚠️ Please enter a product or material description.")
        else:
            with st.spinner("⚡ Running Hybrid Retrieval, Normative Resolution & QCO Compliance Checks..."):
                t_start = time.perf_counter()
                enriched = run_enriched_pipeline(active_q, top_k=top_k, validate=enable_validation)
                t_elapsed = time.perf_counter() - t_start

            if not enriched["is_valid"]:
                st.error(f"❌ Query Rejected by Guardrail: {enriched['validation'].get('reason', 'Invalid query')}")
                st.info("💡 Please specify a civil engineering or building construction material.")
            elif not enriched["results"]:
                st.error("❌ No matching BIS standards found.")
            else:
                # Vernacular Detection Alert
                v_meta = enriched.get("vernacular_meta", {})
                if v_meta.get("is_vernacular", False):
                    st.success(f"🌐 **Vernacular / Multilingual Query Recognized:** Detected terms `{v_meta.get('detected_vernacular_terms')}`. Expanded to standardized technical vocabulary.")

                # Metric Cards Bar
                st.markdown(f"""
                <div style="display: flex; gap: 1rem; margin: 1rem 0;">
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-num">{len(enriched['results'])}</div>
                        <div class="metric-txt">STANDARDS RECOMMENDED</div>
                    </div>
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-num">{t_elapsed:.3f}s</div>
                        <div class="metric-txt">RETRIEVAL & ANALYSIS LATENCY</div>
                    </div>
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-num">{'✅ Passed' if enable_validation else '⚡ Fast (Direct)'}</div>
                        <div class="metric-txt">GUARDRAIL STATUS</div>
                    </div>
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-num">100% Local</div>
                        <div class="metric-txt">OFFLINE / ZERO COST</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### 📋 Recommended Standards & Comprehensive Specification Cards")

                # Iterate through results
                for rank, item in enumerate(enriched["results"], start=1):
                    std_code = item["standard"]
                    title = item["title"]
                    score = item["score"]
                    curr = item["currency"]
                    norm = item["normative"]
                    params = item["parameters"]
                    comp = item["compliance"]
                    tender = item["tender"]

                    # Badges
                    status_badge = f'<span class="badge-active">🟢 {curr["status"]}: {curr["current_version"]}</span>' if curr["is_current"] else f'<span class="badge-superseded">⚠️ SUPERSEDED BY {curr["current_version"]}</span>'
                    qco_badge = f'<span class="badge-qco-mandatory">🛑 MANDATORY QCO (ISI MARK)</span>' if comp.get("is_mandatory") else f'<span class="badge-active">ℹ️ {comp.get("legal_status", "STANDARD")}</span>'

                    # Header card
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div>
                                <span class="rank-pill">#{rank}</span>
                                <span class="standard-code">{std_code}</span>
                                {status_badge}
                                {qco_badge}
                            </div>
                            <div style="font-weight: 700; color: #1e3c72; background: #eef2ff; padding: 0.3rem 0.7rem; border-radius: 8px; font-size: 0.9rem;">
                                Relevance Score: {score}
                            </div>
                        </div>
                        <div style="font-size: 1.05rem; font-weight: 600; color: #2d3748; margin-top: 0.6rem;">
                            {title}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if curr.get("warning_message"):
                        st.markdown(f'<div class="alert-superseded">{curr["warning_message"]}</div>', unsafe_allow_html=True)

                    # Multi-dimensional tabs per recommendation
                    st_tab1, st_tab2, st_tab3, st_tab4, st_tab5 = st.tabs([
                        "📌 Overview & Lifecycle",
                        "🧪 Normative Tests & Allied Codes",
                        "📊 Technical Parameters",
                        "⚖️ QCO & Legal Mandate",
                        "📝 Tender Clause & QA Checklist"
                    ])

                    with st_tab1:
                        st.markdown(f"**Current Active Revision:** `{curr.get('current_version')}`")
                        st.markdown(f"**Lifecycle Status:** `{curr.get('status')}`")
                        if curr.get("consolidation_summary"):
                            st.info(f"ℹ️ **Scope & Revision Summary:** {curr.get('consolidation_summary')}")
                        if curr.get("latest_amendments"):
                            st.markdown("**Active Gazette Amendments:**")
                            for amd in curr.get("latest_amendments", []):
                                st.markdown(f"- **Amendment #{amd['amendment_no']} ({amd['year']}):** {amd['summary']}")

                    with st_tab2:
                        st.markdown("##### 🔬 Mandatory Acceptance & Quality Test Standards")
                        test_methods = norm.get("mandatory_test_methods", [])
                        if test_methods:
                            for tm in test_methods:
                                st.markdown(f"- **`{tm['code']}`**: {tm['title']} *(Type: {tm.get('requirement_type', 'Mandatory Test')})*")
                        else:
                            st.caption("Testing specifications detailed in the primary document.")

                        st.markdown("##### 📐 Allied Codes of Practice & Feedstock Standards")
                        allied = norm.get("allied_codes_of_practice", [])
                        for al in allied:
                            st.markdown(f"- **`{al['code']}`**: {al['title']}")
                        feedstocks = norm.get("feedstock_and_testing_sand", [])
                        for fs in feedstocks:
                            st.markdown(f"- 🧪 *Standard Testing Sand / Feedstock:* **`{fs['code']}`** — {fs['title']}")

                    with st_tab3:
                        if params.get("has_parameters"):
                            p_data = params.get("parameters", {})
                            st.markdown("##### 📏 Quantitative Material Parameters & Clauses")
                            st.json(p_data)
                        else:
                            st.caption("Quantitative parameters follow standard classification thresholds in the code.")

                    with st_tab4:
                        st.markdown("##### 🏛️ Government of India Quality Control Order (QCO)")
                        st.markdown(f"- **Legal Status:** `{comp.get('legal_status')}`")
                        st.markdown(f"- **Certification Scheme:** `{comp.get('certification_scheme')}`")
                        st.markdown(f"- **Issuing Ministry:** `{comp.get('issuing_ministry')}`")
                        st.markdown(f"- **QCO Order Reference:** `{comp.get('qco_name')} ({comp.get('gazette_order_reference')})`")
                        st.markdown(f"- **Statutory Provisions:** `{comp.get('statutory_provisions')}`")
                        st.warning(f"⚠️ **Penalties & Legal Consequences under BIS Act 2016:**\n{comp.get('penalties_and_consequences')}")

                    with st_tab5:
                        st.markdown("##### 📄 Ready-to-Copy Tender Specification Clause")
                        st.code(tender.get("tender_clause_markdown", ""), language="markdown")
                        st.markdown("##### 📋 Actionable Site QA & Bidder Inspection Checklist")
                        for chk in tender.get("qa_checklist", []):
                            st.checkbox(f"**{chk['step']}**: {chk['action']}", value=False, key=f"chk_{rank}_{chk['step']}")

                    st.markdown("---")

# ── TAB 2: Side-by-Side Scope Comparator ────────────────────────────────────────
with tab_compare:
    st.markdown("### 🔄 Side-by-Side Scope Comparator & Disambiguation Engine")
    st.markdown("Compare overlapping standards to determine exact engineering suitability, durability in aggressive environments, and design rules.")
    
    col1, col2 = st.columns(2)
    available_standards = ["IS 269", "IS 1489 (Part 1)", "IS 455", "IS 456", "IS 1343", "IS 4926", "IS 383", "IS 1786", "IS 2116", "IS 3466"]
    
    with col1:
        sel1 = st.selectbox("Select Standard A", available_standards, index=0)
    with col2:
        sel2 = st.selectbox("Select Standard B", available_standards, index=1)
        
    comp_result = comparator.compare_standards([sel1, sel2])
    
    if comp_result.get("comparison_possible"):
        st.success(comp_result.get("selection_guide", ""))
        
        matrix_rows = comp_result.get("matrix", [])
        if matrix_rows:
            st.markdown("#### 📊 Comparative Differentiation Matrix")
            for row in matrix_rows:
                st.markdown(f"**{row['attribute']}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**{sel1}:** {row['values'].get(sel1, 'N/A')}")
                with c2:
                    st.info(f"**{sel2}:** {row['values'].get(sel2, 'N/A')}")
    else:
        st.warning("Please select two distinct standards to view comparative analysis.")

# ── TAB 3: Standards & QCO Registry Browser ─────────────────────────────────────
with tab_registry:
    st.markdown("### 📜 BIS Standards Lifecycle & QCO Registry Browser")
    
    reg_data = currency_mgr.registry
    search_reg = st.text_input("Filter registry by code or title...", placeholder="e.g. IS 269, IS 383, cement, rebar")
    
    for code, info in reg_data.items():
        if search_reg.lower() in code.lower() or search_reg.lower() in info.get("title", "").lower() or not search_reg:
            with st.expander(f"📘 {code}: {info.get('title')} ({info.get('current_version')})"):
                st.markdown(f"- **Current Active Version:** `{info.get('current_version')}`")
                st.markdown(f"- **Status:** `{info.get('status')}`")
                st.markdown(f"- **Consolidation Summary:** {info.get('consolidation_summary')}")
                hist = info.get("historical_versions", [])
                if hist:
                    st.markdown("- **Historical Superseded Versions:**")
                    for h in hist:
                        st.markdown(f"  - `{h['code']}` ({h.get('title')}) — Superseded by `{h.get('superseded_by')}`")
                amds = info.get("latest_amendments", [])
                if amds:
                    st.markdown("- **Gazette Amendments:**")
                    for a in amds:
                        st.markdown(f"  - Amendment #{a['amendment_no']} ({a['year']}): {a['summary']}")

# ── TAB 4: Team BYTEMINDS ───────────────────────────────────────────────────────
with tab_credits:
    st.markdown("""
    # 👥 Developed by Team BYTEMINDS
    
    ### 🏆 Project: BIS Standards Recommendation & Compliance Engine
    
    ---
    
    ### 🚀 Key Technical Contributions:
    1. **Hybrid Retrieval System**: Fusion of Okapi BM25 keyword matching with dense contextual embeddings (`all-MiniLM-L6-v2`).
    2. **Version Control & Currency Tracking**: Full lifecycle status tracking (`ACTIVE`, `SUPERSEDED`, `WITHDRAWN`), modern revision linking, and active amendment tracking.
    3. **Normative Dependency Graph**: Resolution of mandatory testing codes (`IS 4031`, `IS 4032`, `IS 2386`, `IS 1608`) and allied codes of practice (`IS 456`, `IS 4926`).
    4. **Quantitative Parameter Extraction**: Automated structured parameter limit extraction for compressive strengths, setting times, soundness, and grading zones.
    5. **QCO & Regulatory Compliance Layer**: Integration of DPIIT and Ministry Quality Control Orders, Scheme-I Mandatory ISI marking verification, and statutory penalties under the BIS Act 2016.
    6. **Multilingual / Indic NLP Engine**: Seamless normalization and translation of Hindi (Devanagari), Hinglish, and regional vernacular terminology.
    7. **Comparative Scope Disambiguation**: Side-by-side differentiation matrix for overlapping engineering standards.
    8. **Tender Specification & QA Checklist Generator**: Automatic generation of CPWD/PWD-ready tender clauses and site inspection verification checklists.
    
    ---
    *Built with Python, Streamlit, PyTorch, Sentence-Transformers, and Ollama.*
    """)
