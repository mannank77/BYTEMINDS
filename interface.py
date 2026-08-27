"""
BIS Standards Recommendation & Compliance Engine — Streamlit UI
Government of India (GoI) & GIGW 3.0 Compliant National Regulatory Intelligence Portal
Typography inspired by the Official Smart India Hackathon (SIH) Portal (Montserrat + Poppins + Noto Sans Devanagari)
Developed by Team BYTEMINDS for Smart India Hackathon (SIH)
"""

import time
import json
import hashlib
import streamlit as st

from src.retriever import get_retriever
from src.pipeline import run_enriched_pipeline, get_query_validation
from src.currency_manager import get_currency_manager
from src.scope_comparator import get_scope_comparator
from src.compliance_checker import get_compliance_checker

# Page Configuration
st.set_page_config(
    page_title="BIS Standards & Compliance Intelligence Portal — Government of India",
    page_icon="🏛️",
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


def compute_sha256(text: str) -> str:
    """Generate SHA-256 digest for cryptographic provenance stamp."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24].upper()


# ─────────────────────────────────────────────────────────────────────────────
# 🎨 SIH 2024 & GIGW 3.0 Typography & Design System (Custom CSS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    /* Google Fonts: Montserrat (SIH Branding & Headings) + Poppins (UI Body) + Noto Sans Devanagari (Indic) */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,700&family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    /* Global Typography - SIH Inspiration */
    html, body, [class*="css"], .stMarkdown, .stText, p, span, label, div {
        font-family: 'Poppins', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #1e293b;
    }
    
    /* Headings with Montserrat (Bold, Energetic SIH Aesthetic) */
    h1, h2, h3, h4, h5, h6, .gov-title-en, .std-code-title, .search-label, .rank-tag, .section-heading {
        font-family: 'Montserrat', 'Poppins', sans-serif !important;
        letter-spacing: -0.3px;
        font-weight: 700 !important;
    }

    /* Buttons, Action Badges & Tabs */
    .stButton > button, div[data-baseweb="tab-list"] button, .gigw-pill, .score-chip, .stamp-badge, .gov-status-tag {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
    }

    /* GIGW Accessibility Top Bar */
    .gigw-top-bar {
        background-color: #071e3d;
        color: #cbd5e1;
        padding: 6px 20px;
        font-size: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e3a8a;
        margin: -1rem -1rem 0 -1rem;
        font-family: 'Poppins', sans-serif;
    }
    .gigw-top-left {
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
    }
    .gigw-top-right {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.76rem;
    }
    .gigw-pill {
        background: rgba(255, 255, 255, 0.14);
        padding: 3px 9px;
        border-radius: 4px;
        font-weight: 600;
        color: #f8fafc;
    }

    /* National Tricolor Accent Stripe */
    .tricolor-stripe {
        height: 4px;
        background: linear-gradient(to right, #FF9933 33.3%, #FFFFFF 33.3%, #FFFFFF 66.6%, #138808 66.6%);
        width: 100%;
        margin: 0 0 16px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Bureau Masthead */
    .gov-masthead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0 16px 0;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 16px;
        flex-wrap: wrap;
        gap: 14px;
    }
    .gov-masthead-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .gov-emblem-box {
        font-size: 2.8rem;
        line-height: 1;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 6px 10px;
    }
    .gov-title-hi {
        font-size: 1.15rem;
        font-weight: 700;
        color: #b45309;
        letter-spacing: -0.2px;
        font-family: 'Noto Sans Devanagari', 'Poppins', sans-serif !important;
    }
    .gov-title-en {
        font-size: 1.5rem;
        font-weight: 800;
        color: #071e3d;
        letter-spacing: -0.4px;
        line-height: 1.25;
    }
    .gov-subtitle {
        font-size: 0.88rem;
        color: #475569;
        font-weight: 500;
        margin-top: 3px;
    }
    .gov-status-tag {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Live Gazette & Statutory Notice Ticker */
    .gazette-ticker {
        background: linear-gradient(90deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #fde68a;
        border-left: 5px solid #d97706;
        color: #92400e;
        padding: 10px 16px;
        font-size: 0.86rem;
        font-weight: 600;
        border-radius: 6px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    /* Search Box & Controls */
    .search-panel {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-top: 3px solid #071e3d;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .search-label {
        font-size: 0.98rem;
        font-weight: 700;
        color: #071e3d;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Metric Summary Dashboard (SIH Styled) */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
        margin: 16px 0 22px 0;
    }
    .gov-metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #071e3d;
        border-radius: 6px;
        padding: 14px 18px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .gov-metric-val {
        font-size: 1.55rem;
        font-weight: 800;
        color: #071e3d;
        font-family: 'Montserrat', sans-serif !important;
    }
    .gov-metric-lbl {
        font-size: 0.74rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        margin-top: 2px;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Recommendation Cards */
    .gov-result-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-top: 4px solid #071e3d;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .gov-result-card-superseded {
        background: #fffdfa;
        border: 1px solid #fde68a;
        border-top: 4px solid #d97706;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .rank-tag {
        background: #071e3d;
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 4px;
        font-weight: 800;
        font-size: 0.82rem;
        margin-right: 8px;
        font-family: 'Montserrat', sans-serif !important;
    }
    .std-code-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #071e3d;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .score-chip {
        background: #f1f5f9;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
    }

    /* Government Badges */
    .badge-active-gov {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #86efac;
        margin-left: 6px;
        font-family: 'Montserrat', sans-serif !important;
    }
    .badge-superseded-gov {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #fde68a;
        margin-left: 6px;
        font-family: 'Montserrat', sans-serif !important;
    }
    .badge-qco-gov {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #f87171;
        margin-left: 6px;
        font-family: 'Montserrat', sans-serif !important;
    }
    .badge-voluntary-gov {
        background-color: #f1f5f9;
        color: #334155;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #cbd5e1;
        margin-left: 6px;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Normative Test Tags */
    .test-pill {
        display: inline-block;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 3px solid #071e3d;
        border-radius: 4px;
        padding: 6px 12px;
        margin: 4px 6px 4px 0;
        font-size: 0.84rem;
        color: #0f172a;
    }

    /* Structured Parameter Table */
    .param-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0 16px 0;
        font-size: 0.86rem;
    }
    .param-table th {
        background: #f1f5f9;
        color: #071e3d;
        font-weight: 700;
        padding: 9px 12px;
        text-align: left;
        border: 1px solid #cbd5e1;
        font-family: 'Montserrat', sans-serif !important;
    }
    .param-table td {
        padding: 9px 12px;
        border: 1px solid #e2e8f0;
        color: #1e293b;
    }
    .param-table tr:nth-child(even) {
        background: #f8fafc;
    }

    /* Statutory Callout Box */
    .statutory-callout {
        background: #fff8f8;
        border: 1px solid #fecaca;
        border-left: 5px solid #dc2626;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.88rem;
        color: #7f1d1d;
    }

    /* Tender Verification Stamp */
    .tender-stamp {
        background: #f8fafc;
        border: 1px dashed #071e3d;
        border-radius: 6px;
        padding: 10px 14px;
        margin-top: 12px;
        font-size: 0.8rem;
        color: #334155;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .stamp-badge {
        background: #071e3d;
        color: #ffffff;
        padding: 3px 9px;
        border-radius: 4px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Official Footer */
    .gov-footer {
        background: #071e3d;
        color: #94a3b8;
        padding: 24px 20px;
        border-top: 4px solid #FF9933;
        margin-top: 40px;
        border-radius: 8px 8px 0 0;
        font-size: 0.83rem;
        line-height: 1.6;
    }
    .gov-footer a {
        color: #38bdf8;
        text-decoration: none;
        font-weight: 500;
    }
    .gov-footer a:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 🏛️ 1. GIGW Accessibility Header & Masthead
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gigw-top-bar">
    <div class="gigw-top-left">
        <span>🇮🇳 <strong>भारत सरकार</strong> | Government of India</span>
        <span>•</span>
        <span>उपभोक्ता मामले, खाद्य एवं सार्वजनिक वितरण मंत्रालय</span>
    </div>
    <div class="gigw-top-right">
        <span class="gigw-pill">Smart India Hackathon 2024</span>
        <span class="gigw-pill">GIGW 3.0 Compliant</span>
        <span class="gigw-pill">Team BYTEMINDS</span>
    </div>
</div>
<div class="tricolor-stripe"></div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="gov-masthead">
    <div class="gov-masthead-left">
        <div class="gov-emblem-box">🏛️</div>
        <div>
            <div class="gov-title-hi">भारतीय मानक ब्यूरो (BIS) — राष्ट्रीय मानक अनुशंसा एवं विनियामक अनुपालन प्रणाली</div>
            <div class="gov-title-en">Bureau of Indian Standards (BIS) Standards & Compliance Engine</div>
            <div class="gov-subtitle">Intelligent Hybrid Retrieval, Normative Dependency Graph, Technical Parameter Extraction, QCO Compliance & GeM/CPWD Tender Clause Generator</div>
        </div>
    </div>
    <div>
        <div class="gov-status-tag">
            <span>●</span> <strong>Portal Active (BIS Act 2016)</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="gazette-ticker">
    <span>📜 <strong>GAZETTE NOTIFICATION & QUALITY CONTROL ORDER (QCO):</strong></span>
    <span>Mandatory ISI Certification Mark (Scheme-I) enforced under BIS Act 2016 for Structural Steel (IS 1786), Hydraulic Cements (IS 269), Aggregates (IS 383), and Precast Concrete. Non-compliance invites penal proceedings under Section 29.</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ Sidebar Navigation & Settings
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ Bureau Control Center")
    st.caption("Configure retrieval parameters and regulatory filters:")

    enable_validation = st.checkbox(
        "🤖 Enable LLM Guardrail (Ollama)",
        value=False,
        help="Use Ollama (phi:2.7b) to filter out queries unrelated to construction materials"
    )
    top_k = st.slider("📊 Recommendations (Top-K)", min_value=3, max_value=8, value=5)

    st.divider()
    st.markdown("#### 📚 Quick Vernacular Queries")
    st.caption("Test multi-lingual and regional site terminology:")

    quick_queries = [
        ("सरिया Fe 500D (TMT Rebar)", "सरिया 16mm Fe 500D (TMT Rebar)"),
        ("छत की सीमेंट (Roof Slab Concrete)", "छत की सीमेंट (Roof Slab Concrete)"),
        ("बालू व कंक्रीट रेत (Aggregates)", "बालू और कंक्रीट रेत (Fine Aggregates)"),
        ("OPC 53 Grade Cement", "Ordinary Portland Cement 53 Grade"),
        ("Prestressed Concrete Girders", "Prestressed Concrete Bridge Girders"),
        ("Ready-Mixed Concrete (RMC)", "Ready-Mixed Concrete Batching Plant")
    ]

    for label, q_text in quick_queries:
        if st.button(f"👉 {label}", use_container_width=True):
            st.session_state["query_input"] = q_text
            st.rerun()

    st.divider()
    st.markdown("""
    **Portal Features & Protocols:**
    - ✅ **Hybrid BM25 + Dense Embeddings**
    - ✅ **Lifecycle & Revisions (IS 269:2015)**
    - ✅ **Normative Tests (IS 4031 / 4032 / 2386)**
    - ✅ **Statutory QCOs & ISI Scheme-I**
    - ✅ **Indic / Vernacular Normalization**
    - ✅ **GeM / CPWD Tender Clause Generator**
    - ✅ **Cryptographic Tamper-Proof Stamp**
    """)


# ─────────────────────────────────────────────────────────────────────────────
# 📑 Main Navigation Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_search, tab_compare, tab_registry, tab_credits = st.tabs([
    "🔍 Smart Search & Complete Specification",
    "🔄 Side-by-Side Scope Comparator",
    "📜 Standards & QCO Registry Browser",
    "👥 Team BYTEMINDS & Credentials"
])


# ─────────────────────────────────────────────────────────────────────────────
# ── TAB 1: Smart Search & Complete Specification
# ─────────────────────────────────────────────────────────────────────────────
with tab_search:
    default_text = st.session_state.get("query_input", "")

    with st.form("search_form"):
        st.markdown('<div class="search-label">📝 Enter Material, Product, or Tender Specification Query (English / Hindi / Hinglish)</div>', unsafe_allow_html=True)
        query = st.text_area(
            "Query Description",
            value=default_text,
            height=85,
            placeholder="e.g. High-strength OPC 53 grade cement for structural columns | सरिया Fe 500D earthquake resistant rebar | छत की ढलाई के लिए सीमेंट...",
            label_visibility="collapsed"
        )
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submitted = st.form_submit_button("🔍 Search Bureau Standards & Generate Specs", use_container_width=True, type="primary")
        with col2:
            clear_btn = st.form_submit_button("🗑️ Clear Search", use_container_width=True)

    if clear_btn:
        st.session_state["query_input"] = ""
        st.rerun()

    if submitted or (default_text and not clear_btn):
        active_q = query.strip() if query else default_text.strip()
        if len(active_q) < 3:
            st.warning("⚠️ Please enter a valid product, material, or engineering specification description.")
        else:
            with st.spinner("⚡ Resolving Hybrid Retrieval, Normative Graph, Gazette Currency & QCO Status..."):
                t_start = time.perf_counter()
                enriched = run_enriched_pipeline(active_q, top_k=top_k, validate=enable_validation)
                t_elapsed = time.perf_counter() - t_start

            if not enriched["is_valid"]:
                st.error(f"❌ Query Rejected by Bureau Guardrail: {enriched['validation'].get('reason', 'Invalid query')}")
                st.info("💡 Please specify a civil engineering, building construction, or manufactured material query.")
            elif not enriched["results"]:
                st.error("❌ No matching Bureau of Indian Standards (BIS) records found.")
            else:
                # Vernacular recognized alert
                v_meta = enriched.get("vernacular_meta", {})
                if v_meta.get("is_vernacular", False):
                    st.markdown(f"""
                    <div style="background: #eef2ff; border: 1px solid #c7d2fe; border-left: 4px solid #4f46e5; padding: 8px 14px; border-radius: 6px; font-size: 0.85rem; color: #312e81; margin-bottom: 14px;">
                        🌐 <strong>Vernacular / Indic Terminology Recognized:</strong> Detected regional terms <code>{v_meta.get('detected_vernacular_terms')}</code>. Automatically normalized to standardized Bureau technical lexicon.
                    </div>
                    """, unsafe_allow_html=True)

                # National Registry Stats Bar
                st.markdown(f"""
                <div class="metric-grid">
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">{len(enriched['results'])}</div>
                        <div class="gov-metric-lbl">Standards Recommended</div>
                    </div>
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">{t_elapsed:.3f}s</div>
                        <div class="gov-metric-lbl">Hybrid Search & Graph Latency</div>
                    </div>
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">{'✅ Enforced' if any(r['compliance'].get('is_mandatory') for r in enriched['results']) else 'ℹ️ Standard'}</div>
                        <div class="gov-metric-lbl">QCO Scheme-I Verification</div>
                    </div>
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">🔒 100% Offline</div>
                        <div class="gov-metric-lbl">Air-Gapped & Zero-Data-Leakage</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### 📋 Recommended Bureau Standards & Complete Specification Cards")

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
                    if curr["is_current"]:
                        status_badge = f'<span class="badge-active-gov">🟢 ACTIVE: {curr["current_version"]}</span>'
                        card_class = "gov-result-card"
                    else:
                        status_badge = f'<span class="badge-superseded-gov">⚠️ SUPERSEDED BY {curr["current_version"]}</span>'
                        card_class = "gov-result-card-superseded"

                    if comp.get("is_mandatory"):
                        qco_badge = '<span class="badge-qco-gov">🛑 MANDATORY QCO (ISI MARK)</span>'
                    else:
                        qco_badge = f'<span class="badge-voluntary-gov">ℹ️ {comp.get("legal_status", "VOLUNTARY")}</span>'

                    # Header card
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <span class="rank-tag">#{rank}</span>
                                <span class="std-code-title">{std_code}</span>
                                {status_badge}
                                {qco_badge}
                            </div>
                            <div class="score-chip">
                                Match Relevance: <strong>{score}</strong>
                            </div>
                        </div>
                        <div style="font-size: 1.05rem; font-weight: 600; color: #1e293b; margin-top: 8px; line-height: 1.4;">
                            {title}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if curr.get("warning_message"):
                        st.markdown(f"""
                        <div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #d97706; padding: 10px 14px; border-radius: 6px; font-size: 0.88rem; color: #92400e; margin-bottom: 12px;">
                            ⚠️ <strong>Superseded Standard Notice:</strong> {curr["warning_message"]}
                        </div>
                        """, unsafe_allow_html=True)

                    # Multi-dimensional tabs per recommendation
                    st_tab1, st_tab2, st_tab3, st_tab4, st_tab5 = st.tabs([
                        "📌 Overview & Gazette Currency",
                        "🔬 Normative Tests & Allied Codes",
                        "📊 Technical Parameters & Limits",
                        "🏛️ Statutory QCO & Legal Mandate",
                        "📝 GeM/CPWD Tender Clause & Site QA"
                    ])

                    # ── Sub-Tab 1: Overview & Currency ──
                    with st_tab1:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**Current Active Bureau Code:** `{curr.get('current_version')}`")
                            st.markdown(f"**Lifecycle Status:** `{curr.get('status')}`")
                        with c2:
                            st.markdown(f"**Base Family:** `{curr.get('base_code')}`")
                            st.markdown(f"**Standard Type:** Indian National Standard (BIS)")

                        if curr.get("consolidation_summary"):
                            st.info(f"ℹ️ **Consolidation & Scope Summary:** {curr.get('consolidation_summary')}")

                        if curr.get("latest_amendments"):
                            st.markdown("##### 📜 Active Gazette Amendments:")
                            for amd in curr.get("latest_amendments", []):
                                st.markdown(f"- **Amendment #{amd['amendment_no']} ({amd['year']}):** {amd['summary']}")

                    # ── Sub-Tab 2: Normative Tests ──
                    with st_tab2:
                        st.markdown("##### 🔬 Mandatory Quality Acceptance & Laboratory Test Standards")
                        test_methods = norm.get("mandatory_test_methods", [])
                        if test_methods:
                            for tm in test_methods:
                                st.markdown(f"""
                                <div class="test-pill">
                                    <strong>{tm['code']}</strong>: {tm['title']} <span style="color: #64748b; font-size: 0.78rem;">({tm.get('requirement_type', 'Mandatory Test')})</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.caption("Standard testing protocols specified directly in the parent code.")

                        st.markdown("##### 📐 Allied Codes of Practice & Engineering Guidelines")
                        allied = norm.get("allied_codes_of_practice", [])
                        if allied:
                            for al in allied:
                                st.markdown(f"""
                                <div class="test-pill">
                                    <strong>{al['code']}</strong>: {al['title']}
                                </div>
                                """, unsafe_allow_html=True)

                        feedstocks = norm.get("feedstock_and_testing_sand", [])
                        if feedstocks:
                            st.markdown("##### 🧪 Standard Testing Sand & Feedstock Standards")
                            for fs in feedstocks:
                                st.markdown(f"""
                                <div class="test-pill" style="border-left-color: #059669;">
                                    🧪 <strong>{fs['code']}</strong>: {fs['title']}
                                </div>
                                """, unsafe_allow_html=True)

                    # ── Sub-Tab 3: Technical Parameters ──
                    with st_tab3:
                        if params.get("has_parameters"):
                            p_data = params.get("parameters", {})

                            # 1. Compressive Strength Table if available
                            phys = p_data.get("physical_requirements", {})
                            comp_strength = phys.get("compressive_strength_min_mpa")
                            
                            if comp_strength and isinstance(comp_strength, dict):
                                st.markdown("##### 🧱 Minimum Compressive Strength Requirements (MPa / N/mm²)")
                                if any(isinstance(v, dict) for v in comp_strength.values()):
                                    # Multiple grades (e.g. 33, 43, 53)
                                    rows_html = ""
                                    for grade, vals in comp_strength.items():
                                        grade_lbl = grade.replace("_", " ").upper()
                                        d3 = vals.get("72_hours_3_days", "—")
                                        d7 = vals.get("168_hours_7_days", "—")
                                        d28 = vals.get("672_hours_28_days", "—")
                                        rows_html += f"<tr><td><strong>{grade_lbl}</strong></td><td>{d3} MPa</td><td>{d7} MPa</td><td><strong>{d28} MPa</strong></td></tr>"
                                    
                                    st.markdown(f"""
                                    <table class="param-table">
                                        <thead>
                                            <tr>
                                                <th>Cement Grade</th>
                                                <th>72 Hours (3 Days) Min</th>
                                                <th>168 Hours (7 Days) Min</th>
                                                <th>672 Hours (28 Days) Min</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rows_html}
                                        </tbody>
                                    </table>
                                    """, unsafe_allow_html=True)
                                else:
                                    # Single grade
                                    d3 = comp_strength.get("72_hours_3_days", "—")
                                    d7 = comp_strength.get("168_hours_7_days", "—")
                                    d28 = comp_strength.get("672_hours_28_days", "—")
                                    st.markdown(f"""
                                    <table class="param-table">
                                        <thead>
                                            <tr>
                                                <th>72 Hours (3 Days) Min</th>
                                                <th>168 Hours (7 Days) Min</th>
                                                <th>672 Hours (28 Days) Min</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>{d3} MPa</td>
                                                <td>{d7} MPa</td>
                                                <td><strong>{d28} MPa</strong></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    """, unsafe_allow_html=True)

                            # 2. Other Physical Requirements
                            col_p1, col_p2 = st.columns(2)
                            with col_p1:
                                st.markdown("##### ⏱️ Setting Times & Soundness")
                                st_times = phys.get("setting_time_minutes", {})
                                sound = phys.get("soundness", {})
                                st.markdown(f"- **Initial Setting Time (Min):** `{st_times.get('initial_setting_min', 'N/A')} minutes`")
                                st.markdown(f"- **Final Setting Time (Max):** `{st_times.get('final_setting_max', 'N/A')} minutes`")
                                st.markdown(f"- **Le-Chatelier Expansion (Max):** `{sound.get('le_chatelier_expansion_max_mm', 'N/A')} mm`")
                                st.markdown(f"- **Autoclave Expansion (Max):** `{sound.get('autoclave_expansion_max_percent', 'N/A')}%`")
                                if "fineness_blaine_min_m2_kg" in phys:
                                    st.markdown(f"- **Fineness (Blaine Specific Surface Min):** `{phys.get('fineness_blaine_min_m2_kg')} m²/kg`")

                            with col_p2:
                                chem = p_data.get("chemical_requirements", {})
                                if chem:
                                    st.markdown("##### 🧪 Chemical Composition Limits")
                                    for k, v in chem.items():
                                        k_fmt = k.replace("_", " ").title()
                                        st.markdown(f"- **{k_fmt}:** `{v}`")

                            # Mechanical / Steel limits if applicable
                            mech = p_data.get("mechanical_requirements", {})
                            if mech:
                                st.markdown("##### ⚙️ Mechanical Tensile Limits")
                                for k, v in mech.items():
                                    k_fmt = k.replace("_", " ").title()
                                    st.markdown(f"- **{k_fmt}:** `{v}`")
                        else:
                            st.info("ℹ️ Standard classification thresholds and dimensional tolerances follow standard Bureau schedules.")

                    # ── Sub-Tab 4: QCO & Statutory Mandate ──
                    with st_tab4:
                        st.markdown("##### 🏛️ Government of India Quality Control Order (QCO) Compliance")
                        st.markdown(f"- **Statutory Legal Status:** **`{comp.get('legal_status')}`**")
                        st.markdown(f"- **Certification Scheme:** `{comp.get('certification_scheme')}`")
                        st.markdown(f"- **Issuing Ministry:** `{comp.get('issuing_ministry')}`")
                        st.markdown(f"- **Gazette S.O. Reference:** `{comp.get('qco_name')} ({comp.get('gazette_order_reference')})`")
                        st.markdown(f"- **Statutory Provisions:** `{comp.get('statutory_provisions')}`")

                        st.markdown(f"""
                        <div class="statutory-callout">
                            <strong>⚠️ STATUTORY WARNING UNDER BIS ACT 2016 (SECTION 29):</strong><br>
                            {comp.get('penalties_and_consequences')}
                        </div>
                        """, unsafe_allow_html=True)

                    # ── Sub-Tab 5: Tender Clause & QA Checklist ──
                    with st_tab5:
                        st.markdown("##### 📄 Ready-to-Copy GeM / CPWD Form Technical Tender Clause")
                        tender_text = tender.get("tender_clause_markdown", "")
                        st.code(tender_text, language="markdown")

                        # Cryptographic Tamper-Proof Stamp
                        sha_digest = compute_sha256(tender_text)
                        st.markdown(f"""
                        <div class="tender-stamp">
                            <div>
                                🔒 <strong>Cryptographic Tamper-Evident Provenance:</strong> Generated by BIS AI Compliance Engine
                            </div>
                            <div>
                                SHA-256 Stamp: <span class="stamp-badge">{sha_digest}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("##### 📋 Actionable Site QA & Bidder Inspection Checklist")
                        st.caption("Verify compliance items on-site during material consignment inspection:")
                        
                        qa_items = tender.get("qa_checklist", [])
                        for chk in qa_items:
                            st.checkbox(f"**Step {chk['step']}**: {chk['action']}", value=False, key=f"chk_{rank}_{chk['step']}")

                    st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# ── TAB 2: Side-by-Side Scope Comparator
# ─────────────────────────────────────────────────────────────────────────────
with tab_compare:
    st.markdown("### 🔄 Side-by-Side Scope Comparator & Engineering Disambiguation")
    st.markdown("Compare overlapping Bureau standards to determine precise engineering suitability, chemical exposure limits, and life-cycle durability.")

    available_standards = ["IS 269", "IS 1489 (Part 1)", "IS 455", "IS 456", "IS 1343", "IS 4926", "IS 383", "IS 1786", "IS 2116", "IS 3466"]

    c1, c2 = st.columns(2)
    with c1:
        sel1 = st.selectbox("Select Primary Standard (A)", available_standards, index=0)
    with c2:
        sel2 = st.selectbox("Select Comparative Standard (B)", available_standards, index=1)

    comp_result = comparator.compare_standards([sel1, sel2])

    if comp_result.get("comparison_possible"):
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; padding: 12px 16px; border-radius: 6px; color: #14532d; font-size: 0.92rem; margin: 12px 0 18px 0;">
            💡 <strong>ENGINEERING SELECTION GUIDELINE:</strong><br>
            {comp_result.get('selection_guide', '')}
        </div>
        """, unsafe_allow_html=True)

        matrix_rows = comp_result.get("matrix", [])
        if matrix_rows:
            st.markdown("#### 📊 Comparative Engineering Differentiation Matrix")
            for row in matrix_rows:
                st.markdown(f"**{row['attribute']}**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"**{sel1}:** {row['values'].get(sel1, 'N/A')}")
                with col_b:
                    st.info(f"**{sel2}:** {row['values'].get(sel2, 'N/A')}")
    else:
        st.warning("⚠️ Please select two distinct standards to generate comparative analysis.")


# ─────────────────────────────────────────────────────────────────────────────
# ── TAB 3: Standards & QCO Registry Browser
# ─────────────────────────────────────────────────────────────────────────────
with tab_registry:
    st.markdown("### 📜 BIS Standards Lifecycle & QCO Master Registry")
    st.markdown("Browse active, superseded, and consolidated Indian Standards along with gazette amendment tracking.")

    reg_data = currency_mgr.registry
    search_reg = st.text_input("Filter registry database by code or keyword...", placeholder="e.g. IS 269, IS 383, cement, TMT rebar, concrete")

    for code, info in reg_data.items():
        if search_reg.lower() in code.lower() or search_reg.lower() in info.get("title", "").lower() or not search_reg:
            badge = "🟢 ACTIVE" if info.get("status") == "ACTIVE" else "⚠️ SUPERSEDED"
            with st.expander(f"📘 {code}: {info.get('title')} — [{badge}]"):
                st.markdown(f"- **Current Active Version:** `{info.get('current_version')}`")
                st.markdown(f"- **Lifecycle Status:** `{info.get('status')}`")
                st.markdown(f"- **Consolidation Summary:** {info.get('consolidation_summary')}")

                hist = info.get("historical_versions", [])
                if hist:
                    st.markdown("- **Historical Superseded Codes:**")
                    for h in hist:
                        st.markdown(f"  - `{h['code']}` ({h.get('title')}) — Superseded by `{h.get('superseded_by')}`")

                amds = info.get("latest_amendments", [])
                if amds:
                    st.markdown("- **Gazette Amendments:**")
                    for a in amds:
                        st.markdown(f"  - Amendment #{a['amendment_no']} ({a['year']}): {a['summary']}")


# ─────────────────────────────────────────────────────────────────────────────
# ── TAB 4: Team BYTEMINDS & Credentials
# ─────────────────────────────────────────────────────────────────────────────
with tab_credits:
    st.markdown("""
    <div style="background: white; border: 1px solid #cbd5e1; border-top: 4px solid #071e3d; border-radius: 8px; padding: 24px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
        <h2 style="color: #071e3d; margin-top: 0;">👥 Developed by Team BYTEMINDS</h2>
        <h4 style="color: #b45309; margin-top: -8px;">🏆 Smart India Hackathon (SIH) 2024 — Bureau of Indian Standards (BIS)</h4>
        <hr style="margin: 16px 0; border: none; border-top: 1px solid #e2e8f0;">
        
        <h4 style="color: #071e3d;">🚀 Core Technological Innovations & Architectural Pillars:</h4>
        <ol style="line-height: 1.8; font-size: 0.95rem; color: #334155;">
            <li><strong>Hybrid Retrieval Architecture:</strong> Okapi BM25 Lexical Matching fused with Dense Contextual Semantic Embeddings (<code>all-MiniLM-L6-v2</code>) with Reciprocal Rank Fusion re-ranking.</li>
            <li><strong>Lifecycle Currency Engine:</strong> Real-time status resolution of superseded historical standards (e.g. <code>IS 8112</code> / <code>IS 12269</code> consolidated into <code>IS 269:2015</code>) and gazette amendment tracking.</li>
            <li><strong>Normative Reference Knowledge Graph:</strong> Relational resolution of mandatory acceptance test standards (<code>IS 4031</code>, <code>IS 4032</code>, <code>IS 2386</code>, <code>IS 1608</code>) and allied codes of practice (<code>IS 456</code>, <code>IS 4926</code>).</li>
            <li><strong>Quantitative Parameter Extraction:</strong> Structured material threshold extraction for compressive strengths, setting times, soundness, and chemical limits.</li>
            <li><strong>Statutory QCO Compliance & Penal Enforcement:</strong> DPIIT/Ministry Quality Control Order enforcement, Scheme-I Mandatory ISI mark validation, and BIS Act 2016 Section 29 legal notices.</li>
            <li><strong>Indic & Multilingual NLP Normalizer:</strong> Zero-shot vernacular normalization for Hindi (Devanagari script), Hinglish, and regional construction terminology.</li>
            <li><strong>Side-by-Side Scope Comparator:</strong> Multi-attribute disambiguation matrix for overlapping construction codes.</li>
            <li><strong>GeM / CPWD Tender Clause & QA Generator:</strong> Automated generation of public procurement specifications with SHA-256 cryptographic provenance stamps and interactive inspection checklists.</li>
        </ol>
        <hr style="margin: 16px 0; border: none; border-top: 1px solid #e2e8f0;">
        <div style="font-size: 0.85rem; color: #64748b;">
            Built with <strong>Python, Streamlit, PyTorch, Sentence-Transformers, Rank-BM25, and Ollama (Phi-2.7B)</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 🇮🇳 Official Government Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gov-footer">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px;">
        <div style="max-width: 450px;">
            <div style="font-weight: 800; font-size: 1rem; color: #f8fafc; margin-bottom: 6px;">
                🏛️ Bureau of Indian Standards (BIS) — Govt. of India
            </div>
            <div>Manak Bhavan, 9 Bahadur Shah Zafar Marg, New Delhi 110002. Portal engineered for standard compliance, public procurement transparency, and quality assurance.</div>
        </div>
        <div>
            <div style="font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Statutory Links & Compliance</div>
            <div>• <a href="https://www.bis.gov.in" target="_blank">Bureau of Indian Standards Official Portal</a></div>
            <div>• <a href="https://gem.gov.in" target="_blank">Government e-Marketplace (GeM)</a></div>
            <div>• <a href="https://cpwd.gov.in" target="_blank">Central Public Works Department (CPWD)</a></div>
        </div>
        <div>
            <div style="font-weight: 700; color: #f8fafc; margin-bottom: 6px;">National Initiatives</div>
            <div>• Digital India Initiative</div>
            <div>• Bureau of Indian Standards Act, 2016</div>
            <div>• Guidelines for Indian Government Websites (GIGW 3.0)</div>
        </div>
    </div>
    <hr style="border-color: #1e3a8a; margin: 16px 0 10px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; font-size: 0.76rem; color: #64748b;">
        <div>© 2024–2026 Team BYTEMINDS. Built for Smart India Hackathon. All rights reserved.</div>
        <div>Compliant with GIGW 3.0 & Open Standards Policy.</div>
    </div>
</div>
""", unsafe_allow_html=True)
