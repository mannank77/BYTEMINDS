"""
BIS Standards Recommendation & Compliance Engine — Streamlit UI
Government of India (GoI) & GIGW 3.0 Compliant National Regulatory Intelligence Portal
1-Click Instant Language Switcher (English <-> हिन्दी Hindi)
Typography: Montserrat (Headings) + Poppins (UI Body)
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
from src.document_analyzer import get_document_analyzer

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
# 🌐 Multilingual Language Dictionary (1-Click Switcher)
# ─────────────────────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "English": {
        "portal_title": "Bureau of Indian Standards (BIS) Standards & Compliance Engine",
        "portal_sub": "National Regulatory Intelligence, Mandatory QCO Verification & Automated GeM/CPWD Tender Clause Generator",
        "active_status": "Portal Active (BIS Act 2016)",
        "gazette_ticker": "Mandatory ISI Certification Mark (Scheme-I) enforced under BIS Act 2016 for Structural Steel (IS 1786), Hydraulic Cements (IS 269), Aggregates (IS 383), and Precast Concrete. Non-compliance invites penal proceedings under Section 29.",
        "search_label": "Enter Material, Product, or Tender Specification Query",
        "search_placeholder": "e.g. High-strength OPC 53 grade cement for structural columns OR Fe 500D earthquake resistant rebar OR fine aggregates for concrete...",
        "btn_search": "Search Bureau Standards & Generate Specs",
        "btn_clear": "Clear Search",
        "tab_search": "🔍 Smart Search & Complete Specification",
        "tab_compare": "🔄 Side-by-Side Scope Comparator",
        "tab_registry": "📜 Standards & QCO Registry Browser",
        "subtab_overview": "📌 Overview & Gazette Currency",
        "subtab_normative": "🔬 Normative Tests & Allied Codes",
        "subtab_params": "📊 Technical Parameters & Limits",
        "subtab_qco": "🏛️ Statutory QCO & Legal Mandate",
        "subtab_tender": "📝 GeM/CPWD Tender Clause & Site QA",
        "metric_recommended": "Standards Recommended",
        "metric_latency": "Hybrid Search & Graph Latency",
        "metric_qco": "QCO Scheme-I Verification",
        "metric_offline": "Air-Gapped & Zero-Data-Leakage",
        "sidebar_control": "Control Center",
        "sidebar_control_sub": "Search parameters & regulatory filter settings",
        "sidebar_guardrail": "Enable LLM Guardrail (Ollama)",
        "sidebar_topk": "Recommendations Count (Top-K)",
        "sidebar_quick_queries": "Quick Technical Queries",
        "sidebar_protocols": "Verified Engine Protocols",
        "badge_active": "ACTIVE",
        "badge_superseded": "SUPERSEDED BY",
        "badge_qco": "MANDATORY QCO (ISI MARK)",
        "badge_voluntary": "VOLUNTARY / STANDARD",
        "tab_upload": "📄 Document Upload & Compliance Audit",
        "upload_title": "Upload Tender Document for Automated BIS Compliance Audit",
        "upload_desc": "Upload a tender specification, procurement document, or technical schedule (PDF, DOCX, TXT) and the AI engine will automatically detect IS code references, flag outdated standards, identify missing normative test methods, and recommend additional standards.",
        "upload_btn": "Upload tender document (.pdf, .docx, .txt)",
        "upload_analyzing": "Analyzing document — extracting IS codes, checking currency, running compliance audit..."
    },
    "हिन्दी (Hindi)": {
        "portal_title": "भारतीय मानक ब्यूरो (BIS) — मानक एवं विनियामक अनुपालन प्रणाली",
        "portal_sub": "राष्ट्रीय विनियामक बुद्धिमत्ता, अनिवार्य QCO सत्यापन एवं GeM/CPWD निविदा खंड जनरेटर",
        "active_status": "पोर्टल सक्रिय (BIS अधिनियम 2016)",
        "gazette_ticker": "संरचनात्मक स्टील (IS 1786), सीमेंट (IS 269), और कंक्रीट के लिए BIS अधिनियम 2016 के तहत अनिवार्य ISI मार्क (स्कीम-I) लागू। उल्लंघन पर धारा 29 के तहत दंडात्मक कार्यवाही।",
        "search_label": "सामग्री, उत्पाद या निविदा विनिर्देश खोज दर्ज करें",
        "search_placeholder": "उदाहरण: संरचनात्मक कॉलम के लिए उच्च सामर्थ्य OPC 53 सीमेंट या Fe 500D सरिया...",
        "btn_search": "मानक खोजें एवं विनिर्देश जनरेट करें",
        "btn_clear": "खोज साफ़ करें",
        "tab_search": "🔍 स्मार्ट खोज एवं पूर्ण विनिर्देश",
        "tab_compare": "🔄 दायरा तुलना एवं विश्लेषण",
        "tab_registry": "📜 मानक एवं QCO मास्टर रजिस्ट्री",
        "subtab_overview": "📌 अवलोकन एवं राजपत्र स्थिति",
        "subtab_normative": "🔬 अनिवार्य परीक्षण एवं संबद्ध कोड",
        "subtab_params": "📊 तकनीकी पैरामीटर एवं सीमाएं",
        "subtab_qco": "🏛️ विधिक QCO एवं कानूनी आदेश",
        "subtab_tender": "📝 GeM/CPWD निविदा खंड एवं QA चेकलिस्ट",
        "metric_recommended": "अनुशंसित मानक",
        "metric_latency": "खोज एवं विश्लेषण विलंबता",
        "metric_qco": "QCO स्कीम-I सत्यापन",
        "metric_offline": "100% ऑफ़लाइन / डेटा सुरक्षा",
        "sidebar_control": "नियंत्रण केंद्र",
        "sidebar_control_sub": "खोज पैरामीटर एवं विनियामक फ़िल्टर",
        "sidebar_guardrail": "LLM गार्डरेल सक्षम करें (Ollama)",
        "sidebar_topk": "सिफारिशों की संख्या (Top-K)",
        "sidebar_quick_queries": "त्वरित तकनीकी प्रश्न",
        "sidebar_protocols": "सत्यापित इंजन प्रोटोकॉल",
        "badge_active": "सक्रिय",
        "badge_superseded": "द्वारा प्रतिस्थापित",
        "badge_qco": "अनिवार्य QCO (ISI मार्क)",
        "badge_voluntary": "स्वैच्छिक / मानक",
        "tab_upload": "📄 दस्तावेज़ अपलोड एवं अनुपालन लेखापरीक्षा",
        "upload_title": "निविदा दस्तावेज़ अपलोड करें — स्वचालित BIS अनुपालन लेखापरीक्षा",
        "upload_desc": "निविदा विनिर्देश, प्रापण दस्तावेज़, या तकनीकी अनुसूची (PDF, DOCX, TXT) अपलोड करें। AI इंजन स्वचालित रूप से IS कोड संदर्भ, पुराने मानक, लापता परीक्षण विधियाँ पहचानेगा और अतिरिक्त मानकों की सिफारिश करेगा।",
        "upload_btn": "निविदा दस्तावेज़ अपलोड करें (.pdf, .docx, .txt)",
        "upload_analyzing": "दस्तावेज़ विश्लेषण — IS कोड निकालना, मुद्रा जांच, अनुपालन लेखापरीक्षा चल रही है..."
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# 🎨 GIGW 3.0 Typography & Design System (Custom CSS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    /* Google Fonts: Montserrat (Headings) + Poppins (UI Body) + Noto Sans Devanagari */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,700&family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    /* 1. Protect Streamlit Material Symbols / Material Icons from font overrides */
    [data-testid="stIcon"],
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="stSidebarCollapseButton"] span,
    .material-symbols-rounded,
    [class*="material-symbols"],
    [class*="material-icons"],
    span[data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-feature-settings: 'liga' 1;
        letter-spacing: normal !important;
        text-transform: none !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
    }

    /* 0. Completely Hide Streamlit Default Header, Toolbar (Share, Star, Edit, GitHub), Menu & Footer */
    #MainMenu,
    header,
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stAppDeployButton,
    .stActionButton,
    [data-testid="stActionButtonIcon"],
    [data-testid="stToolbarActions"],
    div[data-testid="stToolbarActions"],
    div[data-testid="stStatusWidget"],
    footer {
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Clean top spacing & full-width layout */
    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* 2. Global Typography */
    .stApp, .stMarkdown, .stText, p, label, input, textarea, select {
        font-family: 'Poppins', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1e293b;
    }
    
    /* Headings with Montserrat */
    h1, h2, h3, h4, h5, h6, .gov-title-en, .std-code-title, .search-label, .rank-tag, .section-heading {
        font-family: 'Montserrat', 'Poppins', 'Noto Sans Devanagari', sans-serif !important;
        letter-spacing: -0.3px;
        font-weight: 700 !important;
    }

    /* Buttons, Action Badges & Tabs */
    .stButton > button, div[data-baseweb="tab-list"] button, .gigw-pill, .score-chip, .stamp-badge, .gov-status-tag {
        font-family: 'Montserrat', 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
    }

    /* GIGW Accessibility Top Bar — Full Viewport Edge-to-Edge */
    .gigw-top-bar {
        background-color: #071e3d;
        color: #cbd5e1;
        padding: 8px 2rem;
        font-size: 0.82rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #1e3a8a;
        margin-left: -2rem !important;
        margin-right: -2rem !important;
        margin-top: 0 !important;
        width: calc(100% + 4rem) !important;
        box-sizing: border-box;
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
        gap: 10px;
        font-size: 0.76rem;
    }
    .gigw-pill {
        background: rgba(255, 255, 255, 0.14);
        padding: 3px 9px;
        border-radius: 4px;
        font-weight: 600;
        color: #f8fafc;
    }

    /* National Tricolor Accent Stripe — Full Viewport Edge-to-Edge */
    .tricolor-stripe {
        height: 4px;
        background: linear-gradient(to right, #FF9933 33.3%, #FFFFFF 33.3%, #FFFFFF 66.6%, #138808 66.6%);
        width: calc(100% + 4rem) !important;
        margin-left: -2rem !important;
        margin-right: -2rem !important;
        margin-top: 0 !important;
        margin-bottom: 16px !important;
        box-sizing: border-box;
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
    .gov-title-en {
        font-size: 1.55rem;
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

    /* Language Switcher Bar */
    .lang-toolbar {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 4px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }

    /* Sidebar Clean Styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    .sidebar-header-card {
        background: linear-gradient(135deg, #071e3d 0%, #1e3a8a 100%);
        color: white;
        padding: 14px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(7,30,61,0.15);
    }
    .sidebar-header-title {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sidebar-header-sub {
        font-size: 0.78rem;
        color: #cbd5e1;
        margin-top: 4px;
    }
    .sidebar-section-title {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.82rem;
        font-weight: 700;
        color: #071e3d;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin: 14px 0 8px 0;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        color: #0f172a;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 0.82rem;
        font-weight: 600;
        text-align: left;
        transition: all 0.15s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        width: 100%;
        margin-bottom: 4px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #f1f5f9;
        border-color: #071e3d;
        color: #071e3d;
        transform: translateY(-1px);
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

    /* Metric Summary Dashboard */
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

    /* Official Footer — Full Viewport Edge-to-Edge */
    .gov-footer {
        background: #071e3d;
        color: #94a3b8;
        padding: 28px 2rem;
        border-top: 4px solid #FF9933;
        margin-top: 40px;
        margin-left: -2rem !important;
        margin-right: -2rem !important;
        margin-bottom: -2rem !important;
        width: calc(100% + 4rem) !important;
        box-sizing: border-box;
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
# 🏛️ 1. GIGW Accessibility Top Bar with 1-Click Language Switcher
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gigw-top-bar">
    <div class="gigw-top-left">
        <span><strong>Government of India</strong></span>
        <span>•</span>
        <span>Ministry of Consumer Affairs, Food & Public Distribution</span>
    </div>
    <div class="gigw-top-right">
        <span class="gigw-pill">GIGW 3.0 Compliant</span>
        <span class="gigw-pill">BIS Act 2016</span>
        <span class="gigw-pill">National Portal</span>
    </div>
</div>
<div class="tricolor-stripe"></div>
""", unsafe_allow_html=True)

# Language Selector Bar (100% visible, no clipping)
c_bar1, c_bar2 = st.columns([4, 1.2])
with c_bar1:
    st.caption("🌐 **Official Language Switcher / भाषा चयन:** Switch portal display language instantly with 1-click:")
with c_bar2:
    selected_lang = st.selectbox(
        "Language",
        ["English", "हिन्दी (Hindi)"],
        index=0,
        label_visibility="collapsed",
        key="portal_lang"
    )

T = TRANSLATIONS.get(selected_lang, TRANSLATIONS["English"])

# ─────────────────────────────────────────────────────────────────────────────
# 🏛️ 2. Bureau Masthead
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="gov-masthead">
    <div class="gov-masthead-left">
        <div>
            <div class="gov-title-en">{T['portal_title']}</div>
            <div class="gov-subtitle">{T['portal_sub']}</div>
        </div>
    </div>
    <div>
        <div class="gov-status-tag">
            <span>●</span> <strong>{T['active_status']}</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="gazette-ticker">
    <span>📜 <strong>GAZETTE NOTIFICATION & QUALITY CONTROL ORDER (QCO):</strong></span>
    <span>{T['gazette_ticker']}</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ Clean Redesigned Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-header-card">
        <div class="sidebar-header-title">⚙️ {T['sidebar_control']}</div>
        <div class="sidebar-header-sub">{T['sidebar_control_sub']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">🛡️ AI & Retrieval Settings</div>', unsafe_allow_html=True)
    enable_validation = st.checkbox(
        T["sidebar_guardrail"],
        value=False,
        help="Filters out queries unrelated to construction materials using Ollama (phi:2.7b)"
    )
    
    top_k = st.slider(T["sidebar_topk"], min_value=3, max_value=8, value=5)

    st.markdown(f'<div class="sidebar-section-title">📚 {T["sidebar_quick_queries"]}</div>', unsafe_allow_html=True)
    st.caption("Click any preset query to test standard retrieval:")

    quick_queries = [
        ("TMT Steel Rebar (Fe 500D)", "IS 1786 High Strength Deformed Bars", "16mm Fe 500D TMT Rebar for RCC construction"),
        ("Roof Slab Concrete (OPC 53)", "IS 269 Ordinary Portland Cement", "High strength OPC 53 Grade Cement for roof slab casting"),
        ("Fine Aggregates & M-Sand", "IS 383 Coarse & Fine Aggregates", "Manufactured Sand and fine aggregates for concrete"),
        ("Fly Ash Blended Cement", "IS 1489 Part 1 PPC", "Portland Pozzolana Cement PPC fly ash based"),
        ("Prestressed Bridge Concrete", "IS 1343 Prestressed Concrete", "High-tensile prestressed concrete girders"),
        ("Ready-Mixed Concrete (RMC)", "IS 4926 Ready-Mixed Concrete", "Ready-Mixed Concrete batching plant specifications")
    ]

    for title, sub, full_q in quick_queries:
        if st.button(f"🔍 {title}", help=sub, use_container_width=True, key=f"q_{title}"):
            st.session_state["query_input"] = full_q
            st.rerun()

    st.markdown(f'<div class="sidebar-section-title">🏛️ {T["sidebar_protocols"]}</div>', unsafe_allow_html=True)
    st.markdown("""
    - ⚡ **Hybrid BM25 + Dense Embeddings**
    - 🔄 **Consolidated Lifecycle (IS 269:2015)**
    - 🔬 **Normative Tests (IS 4031/32/2386)**
    - 🛑 **Statutory QCOs & Scheme-I ISI**
    - 🌐 **Zero-Shot Multilingual Processing**
    - 🔒 **SHA-256 Cryptographic Stamp**
    """)


# ─────────────────────────────────────────────────────────────────────────────
# 📑 Main Navigation Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_search, tab_compare, tab_upload, tab_registry = st.tabs([
    T["tab_search"],
    T["tab_compare"],
    T["tab_upload"],
    T["tab_registry"]
])


# ─────────────────────────────────────────────────────────────────────────────
# ── TAB 1: Smart Search & Complete Specification
# ─────────────────────────────────────────────────────────────────────────────
with tab_search:
    default_text = st.session_state.get("query_input", "")

    with st.form("search_form"):
        st.markdown(f'<div class="search-label">📝 {T["search_label"]}</div>', unsafe_allow_html=True)
        query = st.text_area(
            "Query Description",
            value=default_text,
            height=85,
            placeholder=T["search_placeholder"],
            label_visibility="collapsed"
        )
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submitted = st.form_submit_button(f"🔍 {T['btn_search']}", use_container_width=True, type="primary")
        with col2:
            clear_btn = st.form_submit_button(f"🗑️ {T['btn_clear']}", use_container_width=True)

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
                        🌐 <strong>Multilingual Terminology Recognized:</strong> Detected regional terms <code>{v_meta.get('detected_vernacular_terms')}</code>. Automatically normalized to standardized Bureau technical lexicon.
                    </div>
                    """, unsafe_allow_html=True)

                # National Registry Stats Bar
                st.markdown(f"""
                <div class="metric-grid">
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">{len(enriched['results'])}</div>
                        <div class="gov-metric-lbl">{T['metric_recommended']}</div>
                    </div>
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">{t_elapsed:.3f}s</div>
                        <div class="gov-metric-lbl">{T['metric_latency']}</div>
                    </div>
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">{'✅ ' + T['badge_active'] if any(r['compliance'].get('is_mandatory') for r in enriched['results']) else 'ℹ️ Standard'}</div>
                        <div class="gov-metric-lbl">{T['metric_qco']}</div>
                    </div>
                    <div class="gov-metric-card">
                        <div class="gov-metric-val">🔒 100% Offline</div>
                        <div class="gov-metric-lbl">{T['metric_offline']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"### 📋 {T['tab_search']}")

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
                        status_badge = f'<span class="badge-active-gov">🟢 {T["badge_active"]}: {curr["current_version"]}</span>'
                        card_class = "gov-result-card"
                    else:
                        status_badge = f'<span class="badge-superseded-gov">⚠️ {T["badge_superseded"]} {curr["current_version"]}</span>'
                        card_class = "gov-result-card-superseded"

                    if comp.get("is_mandatory"):
                        qco_badge = f'<span class="badge-qco-gov">🛑 {T["badge_qco"]}</span>'
                    else:
                        qco_badge = f'<span class="badge-voluntary-gov">ℹ️ {comp.get("legal_status", T["badge_voluntary"])}</span>'

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
                            ⚠️ <strong>Notice:</strong> {curr["warning_message"]}
                        </div>
                        """, unsafe_allow_html=True)

                    # Multi-dimensional tabs per recommendation
                    st_tab1, st_tab2, st_tab3, st_tab4, st_tab5 = st.tabs([
                        T["subtab_overview"],
                        T["subtab_normative"],
                        T["subtab_params"],
                        T["subtab_qco"],
                        T["subtab_tender"]
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
    st.markdown(f"### {T['tab_compare']}")
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
    st.markdown(f"### {T['tab_registry']}")
    st.markdown("Browse active, superseded, and consolidated Indian Standards along with gazette amendment tracking.")

    reg_data = currency_mgr.registry
    search_reg = st.text_input("Filter registry database by code or keyword...", placeholder="e.g. IS 269, IS 383, cement, TMT rebar, concrete")

    for code, info in reg_data.items():
        if search_reg.lower() in code.lower() or search_reg.lower() in info.get("title", "").lower() or not search_reg:
            badge = f"🟢 {T['badge_active']}" if info.get("status") == "ACTIVE" else f"⚠️ {T['badge_superseded']}"
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
# ── TAB 3: Document Upload & Compliance Audit
# ─────────────────────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown(f"### 📄 {T['upload_title']}")
    st.markdown(f"{T['upload_desc']}")

    uploaded_file = st.file_uploader(
        T["upload_btn"],
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF (tender documents), DOCX (Word specifications), TXT (plain text schedules)",
        key="doc_upload"
    )

    if uploaded_file:
        with st.spinner(T["upload_analyzing"]):
            analyzer = get_document_analyzer()
            try:
                report = analyzer.analyze_document(uploaded_file, uploaded_file.name)
            except Exception as e:
                st.error(f"❌ Document processing failed: {e}")
                st.info("💡 Please ensure the file is a valid PDF, DOCX, or TXT document and is not password-protected.")
                report = None

        if report:
            # ── Document Overview Metrics ──
            st.markdown(f"""
            <div class="metric-grid">
                <div class="gov-metric-card">
                    <div class="gov-metric-val">{report.total_pages}</div>
                    <div class="gov-metric-lbl">Pages / Sections</div>
                </div>
                <div class="gov-metric-card">
                    <div class="gov-metric-val">{report.total_words:,}</div>
                    <div class="gov-metric-lbl">Words Analyzed</div>
                </div>
                <div class="gov-metric-card">
                    <div class="gov-metric-val">{len(report.detected_is_codes)}</div>
                    <div class="gov-metric-lbl">IS Codes Detected</div>
                </div>
                <div class="gov-metric-card">
                    <div class="gov-metric-val">{report.extraction_time:.2f}s</div>
                    <div class="gov-metric-lbl">Analysis Latency</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Compliance Gap Summary ──
            if report.compliance_gaps:
                for gap in report.compliance_gaps:
                    sev = gap.get("severity", "INFO")
                    if sev == "CRITICAL":
                        st.markdown(f"""
                        <div class="statutory-callout">
                            <strong>🚨 CRITICAL COMPLIANCE GAP:</strong> {gap['message']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif sev == "HIGH":
                        st.markdown(f"""
                        <div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 5px solid #d97706; padding: 10px 14px; border-radius: 6px; font-size: 0.88rem; color: #92400e; margin-bottom: 12px;">
                            ⚠️ <strong>HIGH PRIORITY:</strong> {gap['message']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info(f"ℹ️ {gap['message']}")

            # ── Sub-tabs for detailed analysis ──
            doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
                f"🔍 Detected IS Codes ({len(report.detected_is_codes)})",
                f"⚠️ Outdated & Superseded ({len(report.outdated_codes)})",
                f"🔬 Missing Normative References ({len(report.missing_normative)})",
                f"🤖 AI Recommendations ({len(report.recommended_standards)})"
            ])

            # ── Doc Sub-Tab 1: Detected IS Codes ──
            with doc_tab1:
                if report.detected_is_codes:
                    st.markdown("##### All Indian Standard References Found in Document")
                    for idx, code in enumerate(report.detected_is_codes, 1):
                        if code.is_current:
                            badge_html = f'<span class="badge-active-gov">🟢 {T["badge_active"]}: {code.current_version}</span>'
                            card_class = "gov-result-card"
                        else:
                            badge_html = f'<span class="badge-superseded-gov">⚠️ {T["badge_superseded"]} {code.current_version}</span>'
                            card_class = "gov-result-card-superseded"

                        year_display = f": {code.year}" if code.year else ""

                        st.markdown(f"""
                        <div class="{card_class}" style="padding: 12px 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                                <div>
                                    <span class="rank-tag">#{idx}</span>
                                    <span class="std-code-title">{code.standard_id}{year_display}</span>
                                    {badge_html}
                                </div>
                                <div class="score-chip">
                                    Status: <strong>{code.currency_status}</strong>
                                </div>
                            </div>
                            <div style="font-size: 0.85rem; color: #475569; margin-top: 6px; font-style: italic; border-left: 3px solid #cbd5e1; padding-left: 10px;">
                                "...{code.line_context}..."
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("ℹ️ No IS code references were detected in this document.")

            # ── Doc Sub-Tab 2: Outdated Standards ──
            with doc_tab2:
                if report.outdated_codes:
                    st.markdown("##### ⚠️ Standards Referenced That Are Superseded or Outdated")
                    st.markdown("""<div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 5px solid #d97706; padding: 10px 14px; border-radius: 6px; font-size: 0.88rem; color: #92400e; margin-bottom: 16px;">
                        <strong>Tender Quality Alert:</strong> The following standards referenced in your document have been superseded. Using outdated standards in tender specifications may lead to procurement disputes, contract ambiguity, or non-compliant supply.
                    </div>""", unsafe_allow_html=True)

                    for code in report.outdated_codes:
                        year_display = f": {code.year}" if code.year else ""
                        st.markdown(f"""
                        <div class="gov-result-card-superseded" style="padding: 12px 16px;">
                            <div>
                                <span class="std-code-title" style="color: #92400e;">{code.standard_id}{year_display}</span>
                                <span style="font-size: 1.1rem; margin: 0 8px;">→</span>
                                <span class="std-code-title" style="color: #065f46;">{code.current_version}</span>
                                <span class="badge-active-gov">✅ USE THIS</span>
                            </div>
                            <div style="font-size: 0.85rem; color: #92400e; margin-top: 6px;">
                                {code.warning}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; padding: 12px 16px; border-radius: 6px; color: #14532d; font-size: 0.92rem;">
                        ✅ <strong>All Clear:</strong> All IS codes referenced in this document appear to be current and active versions. No superseded standards detected.
                    </div>
                    """, unsafe_allow_html=True)

            # ── Doc Sub-Tab 3: Missing Normative References ──
            with doc_tab3:
                if report.missing_normative:
                    st.markdown("##### 🔬 Mandatory Test Methods & Normative References NOT Found in Document")
                    st.markdown("""<div style="background: #fef2f2; border: 1px solid #fecaca; border-left: 5px solid #dc2626; padding: 10px 14px; border-radius: 6px; font-size: 0.88rem; color: #7f1d1d; margin-bottom: 16px;">
                        <strong>Specification Completeness Alert:</strong> The following mandatory test methods and normative references are required by the standards in your document but are not mentioned. Omitting these may result in incomplete QA verification and contractual disputes.
                    </div>""", unsafe_allow_html=True)

                    for nm in report.missing_normative:
                        st.markdown(f"""
                        <div class="test-pill" style="border-left-color: #dc2626; margin-bottom: 8px; padding: 10px 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <div>
                                    <strong style="color: #dc2626;">❌ MISSING:</strong>
                                    <strong>{nm['missing_code']}</strong>: {nm['missing_title']}
                                </div>
                                <div style="font-size: 0.78rem; color: #64748b;">
                                    Required by: <strong>{nm['parent_standard']}</strong> | Type: {nm['type']}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 5px solid #16a34a; padding: 12px 16px; border-radius: 6px; color: #14532d; font-size: 0.92rem;">
                        ✅ <strong>Normative Check Passed:</strong> No critical missing normative references detected, or the document does not reference standards with tracked normative dependencies.
                    </div>
                    """, unsafe_allow_html=True)

            # ── Doc Sub-Tab 4: AI Recommendations ──
            with doc_tab4:
                if report.recommended_standards:
                    st.markdown("##### 🤖 AI-Recommended Standards Based on Product Descriptions in Document")
                    st.markdown("The AI engine extracted product descriptions from your document and identified additional relevant standards that should be considered:")

                    for rec in report.recommended_standards:
                        st.markdown(f"""
                        <div style="background: #eef2ff; border: 1px solid #c7d2fe; border-left: 4px solid #4f46e5; padding: 10px 14px; border-radius: 6px; font-size: 0.88rem; color: #312e81; margin: 10px 0;">
                            🔍 <strong>Extracted Query:</strong> "{rec['query']}"
                        </div>
                        """, unsafe_allow_html=True)

                        for r in rec.get("recommendations", []):
                            mandatory_badge = '<span class="badge-qco-gov">🛑 MANDATORY QCO</span>' if r.get("is_mandatory") else ""
                            st.markdown(f"""
                            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 3px solid #071e3d; padding: 10px 14px; border-radius: 4px; margin: 6px 0 6px 20px;">
                                <span class="std-code-title" style="font-size: 1.05rem;">{r['standard']}</span>
                                {mandatory_badge}
                                <span class="score-chip" style="margin-left: 8px;">Score: {r['score']}</span>
                                <div style="font-size: 0.88rem; color: #475569; margin-top: 4px;">{r['title']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                elif report.detected_products:
                    st.info("ℹ️ Product descriptions were detected but no additional standard recommendations were generated. The referenced standards may already cover the scope.")
                else:
                    st.info("ℹ️ No product descriptions could be extracted from this document for AI analysis. Try uploading a document with explicit material or product specifications.")

            # ── Download Analysis Report ──
            st.markdown("---")
            st.markdown("##### 📥 Download Compliance Audit Report")

            report_lines = []
            report_lines.append(f"BIS COMPLIANCE AUDIT REPORT")
            report_lines.append(f"=" * 60)
            report_lines.append(f"Document: {report.filename}")
            report_lines.append(f"Pages: {report.total_pages} | Words: {report.total_words:,} | Analysis Time: {report.extraction_time:.2f}s")
            report_lines.append(f"")
            report_lines.append(f"IS CODES DETECTED: {len(report.detected_is_codes)}")
            report_lines.append(f"-" * 40)
            for c in report.detected_is_codes:
                status_mark = "✅ CURRENT" if c.is_current else f"⚠️ SUPERSEDED → {c.current_version}"
                report_lines.append(f"  {c.standard_id}{':' + c.year if c.year else ''} — {status_mark}")
            report_lines.append(f"")
            report_lines.append(f"OUTDATED STANDARDS: {len(report.outdated_codes)}")
            report_lines.append(f"-" * 40)
            for c in report.outdated_codes:
                report_lines.append(f"  {c.standard_id}{':' + c.year if c.year else ''} → Replace with {c.current_version}")
                report_lines.append(f"    Reason: {c.warning}")
            report_lines.append(f"")
            report_lines.append(f"MISSING NORMATIVE REFERENCES: {len(report.missing_normative)}")
            report_lines.append(f"-" * 40)
            for nm in report.missing_normative:
                report_lines.append(f"  ❌ {nm['missing_code']}: {nm['missing_title']}")
                report_lines.append(f"     Required by: {nm['parent_standard']} | Type: {nm['type']}")
            report_lines.append(f"")
            report_lines.append(f"COMPLIANCE GAPS: {len(report.compliance_gaps)}")
            report_lines.append(f"-" * 40)
            for gap in report.compliance_gaps:
                report_lines.append(f"  [{gap['severity']}] {gap['message']}")
            report_lines.append(f"")
            report_lines.append(f"AI RECOMMENDATIONS: {len(report.recommended_standards)}")
            report_lines.append(f"-" * 40)
            for rec in report.recommended_standards:
                report_lines.append(f"  Query: \"{rec['query']}\"")
                for r in rec.get("recommendations", []):
                    report_lines.append(f"    → {r['standard']}: {r['title']} (Score: {r['score']})")
            report_lines.append(f"")
            report_lines.append(f"=" * 60)
            report_lines.append(f"Generated by BIS Standards & Compliance Engine — Government of India")
            report_lines.append(f"SHA-256 Audit Stamp: {compute_sha256(chr(10).join(report_lines))}")

            report_text = "\n".join(report_lines)
            st.download_button(
                label="📥 Download Full Compliance Audit Report (.txt)",
                data=report_text,
                file_name=f"BIS_Compliance_Audit_{report.filename.rsplit('.', 1)[0]}.txt",
                mime="text/plain",
                use_container_width=True
            )


# ─────────────────────────────────────────────────────────────────────────────
# 🇮🇳 Official Government Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gov-footer">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px;">
        <div style="max-width: 450px;">
            <div style="font-weight: 800; font-size: 1rem; color: #f8fafc; margin-bottom: 6px;">
                Bureau of Indian Standards (BIS) — Govt. of India
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
        <div>© Bureau of Indian Standards (BIS), Ministry of Consumer Affairs, Food & Public Distribution. All rights reserved.</div>
        <div>Compliant with GIGW 3.0 & Open Standards Policy.</div>
    </div>
</div>
""", unsafe_allow_html=True)
