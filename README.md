# 🏗️ BIS Standards Recommendation & Compliance Engine

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![LanceDB](https://img.shields.io/badge/LanceDB-VectorDB-6C3CE1.svg)](https://lancedb.com/)
[![Framework](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![Embeddings](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-orange.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![LLM](https://img.shields.io/badge/Ollama-phi:2.7b-green.svg)](https://ollama.ai/)
[![Evaluation](https://img.shields.io/badge/Hit%20Rate%403-100%25-brightgreen.svg)](#-evaluation--benchmark-performance)
[![Languages](https://img.shields.io/badge/Multilingual-EN%20%7C%20HI%20%7C%20TE%20%7C%20TA%20%7C%20BN-yellowgreen.svg)](#-multilingual--vernacular-nlp-support)
[![Team](https://img.shields.io/badge/Developed%20By-Team%20BYTEMINDS-purple.svg)](#-team-credentials--credits)

---

## 📖 Overview

The **BIS Standards Recommendation & Compliance Engine** is a comprehensive AI-powered regulatory search, specification extraction, and compliance intelligence system developed by **Team BYTEMINDS**.

Powered by **LanceDB** (a high-performance embedded vector database), it enables Micro, Small, and Medium Enterprises (MSMEs), structural engineers, contractors, and public procurement officers to instantly retrieve applicable **Bureau of Indian Standards (BIS / IS codes)** in sub-second latency, alongside:

- ⚡ **Embedded Vector Search:** LanceDB combining dense semantic retrieval with BM25-style lexical matching — no Docker, no external services required.
- 🔄 **Lifecycle & Currency Tracking** (Detecting superseded historical standards & active amendments).
- 🧪 **Normative Reference Dependency Graph** (Mandatory testing standards e.g., IS 4031/4032/2386 & allied practice codes).
- 📊 **Quantitative Technical Parameter Extraction** (Compressive strength curves, setting times, fineness, silt limits).
- 🛑 **Government Quality Control Order (QCO) Compliance** (Mandatory Scheme-I ISI Mark validation & BIS Act penal notices).
- 🌐 **Multilingual & Vernacular NLP** (Native processing of Hindi, Telugu, Tamil, Bengali scripts and Hinglish transliterations).
- ⚖️ **Side-by-Side Scope Disambiguation** (Comparative matrices for overlapping standards).
- 📝 **Tender Specification & Site QA Checklist Generator** with **PDF / DOCX Export** (CPWD/PWD contract clauses and inspection checklists).

---

## ⚙️ System Architecture & Working

```
                  ┌──────────────────────────────────────────────────────┐
                  │  Multilingual Query Input (EN / HI / TE / TA / BN)   │
                  │  e.g. "సిమెంట్ గ్రేడ్" / "सरिया Fe 500D" / "சிமெண்ட்"  │
                  └──────────────────────┬───────────────────────────────┘
                                         │
                    [ Vernacular & Indic NLP Normalizer ]
                    (Translates & expands Telugu, Tamil, Bengali,
                     Hindi Devanagari, and Hinglish terminology)
                                         │
                                         ▼
                   [ Optional LLM Guardrail / Validation ]
                   (Ollama Phi-2.7B filters out non-building queries)
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             Query Expansion Engine           │
                  │   (Injects technical synonyms & BIS terms)   │
                  └──────────────┬────────────────┬──────────────┘
                                 │                │
                ┌────────────────┴────┐      ┌────┴────────────────┐
                │   BM25 Lexical      │      │   Dense Semantic    │
                │   Search (40%)      │      │   Embeddings (60%)  │
                │                     │      │                     │
                │ • Exact standard ID │      │ • all-MiniLM-L6-v2  │
                │ • Title / Mat boosts│      │ • Cosine similarity │
                │ • Keyword matching  │      │ • LanceDB vectors   │
                └────────────────┬────┘      └────┬────────────────┘
                                 │                │
                                 └───────┬────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │           Score Fusion & Re-Ranking          │
                  │        (Weighted Combination of Scores)      │
                  └──────────────────────┬───────────────────────┘
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ▼                                 ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│  Lifecycle Currency  │      │ Normative Graph & QA │      │   QCO & Regulatory   │
│  • Active/Superseded │      │ • Test codes (4031)  │      │   • Mandatory ISI    │
│  • Latest Revisions  │      │ • Physical / Chemical│      │   • Ministry Orders  │
│  • Active Amendments │      │ • Allied codes (456) │      │   • Penalties Notice │
└──────────────┬───────┘      └──────────┬───────────┘      └──────────┬───────────┘
               │                         │                             │
               └─────────────────────────┼─────────────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │        Interactive Multi-Tab Dashboard       │
                  │  • Specification Cards • Scope Comparator    │
                  │  • Tender Clauses • Site QA Checklists       │
                  │  • PDF / DOCX Export • Language Switcher     │
                  └──────────────────────────────────────────────┘
```

---

## 🎯 Solutions to Critical Industry Challenges

### 1. 🔄 Version Control & Currency Tracking
- **The Gap**: Static handbooks (like SP 21) contain older historical standards (e.g., `IS 269: 1989` or `IS 383: 1970`).
- **Our Solution (`src/currency_manager.py`)**:
  - Automatically identifies whether an indexed code is `ACTIVE`, `SUPERSEDED`, or `WITHDRAWN`.
  - Maps historical versions to modern consolidated standards (e.g., `IS 269:2015` consolidating 33, 43, and 53 grade OPC; `IS 383:2016` incorporating M-Sand and Recycled Aggregate).
  - Displays high-priority deprecation alerts and summaries of recent gazette amendments.

### 2. 🧪 Specification Completeness & Normative Dependency Graph
- **The Gap**: Returning only a standard ID leaves out mandatory testing methods and technical requirement parameters.
- **Our Solution (`src/normative_tracker.py` & `src/parameter_extractor.py`)**:
  - Relational knowledge graph mapping primary standards to:
    - **Mandatory Test Methods**: Physical testing (`IS 4031 Parts 1-15`), Chemical analysis (`IS 4032`), Aggregate grading (`IS 2386`), Steel tensile testing (`IS 1608 / IS 1599`).
    - **Allied Practice Codes**: Plain/Reinforced Concrete (`IS 456`), Ready-Mixed Concrete (`IS 4926`), Ductile Detailing (`IS 13920`).
    - **Feedstock Standards**: Testing Sand (`IS 650`), Granulated Slag (`IS 12089`), Fly Ash (`IS 3812`).
  - Structured extraction of quantitative parameters (Compressive Strengths at 3d/7d/28d, Setting Times, Soundness, Fineness, Silt content, Chemical limits).

### 3. 🛑 Regulatory & QCO Compliance Framework
- **The Gap**: Procurement officers lacked visibility into government compliance mandates and compulsory certification schemes.
- **Our Solution (`src/compliance_checker.py`)**:
  - Direct integration of Quality Control Orders issued by DPIIT, Ministry of Steel, MoHUA, and Ministry of Road Transport.
  - Flags mandatory Scheme-I ISI Mark requirements vs Compulsory Registration Scheme (CRS) vs National Building Code mandates.
  - Injects statutory legal citations and criminal liability notices under Section 16 & Section 29 of the BIS Act, 2016.

### 4. 🌐 Multilingual & Vernacular NLP Support
- **The Gap**: Purely English models fail when Indian contractors or procurement staff search using vernacular terms.
- **Our Solution (`src/vernacular_normalizer.py`)**:
  - Native recognition of **Hindi** (Devanagari): `"सरिया"`, `"छत की सीमेंट"`, `"बालू"`.
  - Native recognition of **Telugu** script: e.g., `"ఇసుక"` (sand), `"సిమెంట్"` (cement), `"రాడ్"` (rebar).
  - Native recognition of **Tamil** script: e.g., `"மணல்"` (sand), `"சிமெண்ட்"` (cement), `"இரும்பு"` (iron/rebar).
  - Native recognition of **Bengali** script: e.g., `"বালি"` (sand), `"সিমেন্ট"` (cement), `"রড"` (rebar).
  - Phonetic **Hinglish** queries: `"sariya 16mm"`, `"chhat ki cement"`, `"balu grading"`.
  - The entire Streamlit dashboard UI can be switched to Telugu, Tamil, or Bengali via the top navigation language selector.

### 5. ⚖️ Overlapping Scopes & Comparative Differentiation
- **The Gap**: Returns multiple candidate codes without explaining why Standard A applies over Standard B.
- **Our Solution (`src/scope_comparator.py`)**:
  - Side-by-side comparative decision matrix evaluating:
    - Structural application suitability (e.g., `IS 456` RCC vs `IS 1343` Prestressed Concrete).
    - Environmental durability & sulphate resistance (e.g., `IS 269` OPC vs `IS 1489` PPC vs `IS 455` PSC).
    - Heat of hydration, curing durations, and cost/sustainability factors.

### 6. 📝 Tender Clause & Site QA Checklist Generator with Export
- **The Gap**: Engineers lacked copy-pasteable, legally defensible tender specifications — and had no way to directly upload them to procurement portals.
- **Our Solution (`src/tender_generator.py` + `interface.py`)**:
  - Auto-generates CPWD / PWD / PSU-compliant technical specification clauses.
  - Generates actionable 5-step site inspection checklists covering ISI license verification, MTC validation, age limits (>90 days re-testing), and mandatory cube sampling frequencies.
  - **New: One-click Download as PDF or DOCX** — ready for direct upload to GeM / CPWD / e-procurement portals.

---

## 💻 Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Search Engine** | **LanceDB** | Embedded vector database for dense semantic retrieval — zero infrastructure, no Docker required |
| **Interactive Dashboard** | **Streamlit** | Multi-tab UI with smart search, parameter cards, scope comparator, language switcher, and export |
| **Semantic AI & Embeddings** | **Sentence-Transformers (`all-MiniLM-L6-v2`)** | 384-dimensional dense semantic vector encoding for contextual material search |
| **Deep Learning Engine** | **PyTorch (torch, torchvision)** | Backend neural engine optimized for lightweight CPU inference |
| **LLM Guardrails** | **Ollama (`phi:2.7b`)** | Zero-latency local LLM query classification and out-of-domain query guardrail |
| **Multilingual NLP** | **Vernacular Normalizer & Indic Lexicon** | Hindi, Telugu, Tamil, Bengali script tokenization, transliteration, and technical expansion |
| **Export Engine** | **python-docx / fpdf2** | One-click PDF and DOCX generation for tender documents and QA checklists |
| **Data Store** | **Structured JSON + LanceDB** | Real-time indexed catalog with normative graph and compliance stores |
| **Evaluation Suite** | **Custom Benchmark Engine (`eval_script.py`)** | Automated evaluation calculating Hit Rate@3, Hit Rate@5, MRR@5, and Latency |

---

## 📊 Evaluation & Benchmark Performance

Tested against the official benchmark evaluation dataset (`public_test_set.json`):

```
========================================
   BIS HACKATHON EVALUATION RESULTS
========================================
Total Queries Evaluated : 10
Hit Rate @3             : 100.00%   (Target: >80%)
MRR @5                  : 0.9500    (Target: >0.7)
Avg Latency             : 2.88 sec  (Target: <5 seconds)
========================================
```

---

## 👥 Team Credentials & Credits

```
  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║                       TEAM BYTEMINDS                          ║
  ║            Engineering Intelligent Search Solutions           ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝
```

* **Team Name:** BYTEMINDS
* **Project:** BIS Standards Recommendation & Compliance Engine
* **Core Modules Developed:**
  1. **LanceDB Hybrid Search Architecture** (Dense Semantic + BM25 Lexical, fully embedded).
  2. Standards Lifecycle & Currency Tracking Engine.
  3. Normative Reference & Testing Dependency Graph.
  4. Structured Technical Parameter Extraction Engine.
  5. Quality Control Order (QCO) Regulatory Framework.
  6. Indic / Vernacular / Multilingual Query Normalizer (HI, TE, TA, BN + Hinglish).
  7. Full UI Language Switcher (Telugu, Tamil, Bengali dashboards).
  8. Comparative Scope Disambiguation Matrix.
  9. CPWD/PWD Tender Specification & QA Checklist Generator with PDF/DOCX Export.
  10. Interactive Streamlit Web Application & Benchmark Suite.

---

## 🚀 Quick Start & Usage

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/mannank77/BYTEMINDS.git
cd BYTEMINDS

# Install Python dependencies
pip install -r requirements.txt
```

> **No Docker or external services needed.** LanceDB runs fully embedded.

### 2. (Optional) Migrate / Re-Index Data into LanceDB

```bash
python migrate_to_lancedb.py
```

### 3. Launch the Interactive Web Dashboard

```bash
streamlit run interface.py
```

### 4. Run Automated Capability Verification Suite

```bash
python test_all_features.py
```

### 5. Run Batch Inference & Benchmark Evaluation

```bash
# Run batch inference
python inference.py --input public_test_set.json --output results.json

# Calculate evaluation metrics
python eval_script.py --results results.json
```

---

## 📁 Repository Structure

```
BYTEMINDS/
├── data/
│   ├── processed_data.json      # Indexed BIS standards documentation
│   ├── embeddings.npy           # Precomputed semantic vector embeddings
│   ├── standards_registry.json  # Lifecycle currency & revision registry
│   ├── normative_graph.json     # Test standards & allied code dependency graph
│   ├── parameters_db.json       # Quantitative physical & chemical parameters
│   ├── qco_compliance.json      # Government QCO orders & mandatory ISI database
│   └── vernacular_lexicon.json  # Hindi, Telugu, Tamil & Bengali construction terms
├── docs/
│   └── SEARCH_ENGINE_UPGRADE_ANALYSIS.md  # Search engine architectural comparison
├── src/
│   ├── retriever.py             # LanceDB hybrid search engine
│   ├── pipeline.py              # Master pipeline orchestrator & enriched workflow
│   ├── currency_manager.py      # Version control & currency manager
│   ├── normative_tracker.py     # Normative dependency resolver
│   ├── parameter_extractor.py   # Technical parameter extractor
│   ├── compliance_checker.py    # QCO regulatory inspector
│   ├── vernacular_normalizer.py # Multilingual & Indic NLP normalizer (HI/TE/TA/BN)
│   ├── scope_comparator.py      # Comparative differentiation engine
│   ├── tender_generator.py      # Tender specification & QA checklist generator
│   └── llm_classifier.py        # Local Ollama query guardrail
├── migrate_to_lancedb.py        # One-time LanceDB ingestion script
├── test_all_features.py         # Automated verification suite
├── test_db_lifecycle.py         # LanceDB lifecycle tests
├── test_document_analyzer.py    # Document analyzer tests
├── eval_script.py               # Benchmark evaluation script
├── inference.py                 # CLI batch inference script
├── interface.py                 # Interactive Streamlit Web Application
├── backend_app.py               # Backend API layer
├── public_test_set.json         # Benchmark evaluation dataset
├── results.json                 # Latest benchmark test results
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```
