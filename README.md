# 🏗️ BIS Standards Recommendation & Compliance Engine

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![Embeddings](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-orange.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![LLM](https://img.shields.io/badge/Ollama-phi:2.7b-green.svg)](https://ollama.ai/)
[![Evaluation](https://img.shields.io/badge/Hit%20Rate%403-100%25-brightgreen.svg)](#-evaluation--benchmark-performance)
[![Team](https://img.shields.io/badge/Developed%20By-Team%20BYTEMINDS-purple.svg)](#-team-credentials--credits)

---

## 📖 Overview

The **BIS Standards Recommendation & Compliance Engine** is a comprehensive AI-powered regulatory search, specification extraction, and compliance intelligence system developed by **Team BYTEMINDS**.

It enables Micro, Small, and Medium Enterprises (MSMEs), structural engineers, contractors, and public procurement officers to instantly retrieve applicable **Bureau of Indian Standards (BIS / IS codes)** in sub-second latency, alongside:
- 🔄 **Lifecycle & Currency Tracking** (Detecting superseded historical standards & active amendments).
- 🧪 **Normative Reference Dependency Graph** (Mandatory testing standards e.g., IS 4031/4032/2386 & allied practice codes).
- 📊 **Quantitative Technical Parameter Extraction** (Compressive strength curves, setting times, fineness, silt limits).
- 🛑 **Government Quality Control Order (QCO) Compliance** (Mandatory Scheme-I ISI Mark validation & BIS Act penal notices).
- 🌐 **Multilingual & Vernacular NLP** (Native processing of Hindi in Devanagari script, Hinglish, and regional construction terms).
- ⚖️ **Side-by-Side Scope Disambiguation** (Comparative matrices for overlapping standards).
- 📝 **Tender Specification & Site QA Checklist Generator** (CPWD/PWD contract clauses and inspection checklists).

---

## ⚙️ System Architecture & Working

```
                  ┌──────────────────────────────────────────────┐
                  │    Multilingual Query Input (EN / HI / Hing)  │
                  │   e.g. "सरिया Fe 500D" / "छत की सीमेंट" / "OPC 53" │
                  └──────────────────────┬───────────────────────┘
                                         │
                    [ Vernacular & Indic NLP Normalizer ]
                    (Translates & expands regional terminology)
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
                │ • Keyword matching  │      │ • Vector caching    │
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
  - Native recognition of Hindi in Devanagari script (e.g., `"सरिया"`, `"छत की सीमेंट"`, `"बालू"`, `"रोड़ी"`, `"राख वाली ईंट"`).
  - Handles phonetic Hinglish queries (e.g., `"sariya 16mm"`, `"chhat ki cement"`, `"balu grading"`).
  - Translates and enriches queries into standardized technical vocabulary prior to hybrid retrieval.

### 5. ⚖️ Overlapping Scopes & Comparative Differentiation
- **The Gap**: Returns multiple candidate codes without explaining why Standard A applies over Standard B.
- **Our Solution (`src/scope_comparator.py`)**:
  - Side-by-side comparative decision matrix evaluating:
    - Structural application suitability (e.g., `IS 456` RCC vs `IS 1343` Prestressed Concrete).
    - Environmental durability & sulphate resistance (e.g., `IS 269` OPC vs `IS 1489` PPC vs `IS 455` PSC).
    - Heat of hydration, curing durations, and cost/sustainability factors.

### 6. 📝 Tender Clause & Site QA Checklist Generator
- **The Gap**: Engineers lacked copy-pasteable, legally defensible tender specifications and on-site testing checklists.
- **Our Solution (`src/tender_generator.py`)**:
  - Auto-generates CPWD / PWD / PSU-compliant technical specification clauses.
  - Generates actionable 5-step site inspection checklists covering ISI license verification, MTC validation, age limits (>90 days re-testing), and mandatory cube sampling frequencies.

---

## 💻 Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Interactive Dashboard** | **Streamlit** | Multi-tab UI featuring smart search, parameter cards, scope comparator, and registry browser |
| **Semantic AI & Embeddings** | **Sentence-Transformers (`all-MiniLM-L6-v2`)** | 384-dimensional dense semantic vector encoding for contextual material search |
| **Deep Learning Engine** | **PyTorch (torch, torchvision)** | Backend neural engine optimized for lightweight CPU inference |
| **Lexical Engine** | **Custom Okapi BM25** | Term frequency saturation scoring with material keywords and title weighting |
| **LLM Guardrails** | **Ollama (`phi:2.7b`)** | Zero-latency local LLM query classification and out-of-domain query guardrail |
| **Multilingual NLP** | **Vernacular Normalizer & Indic Lexicon** | Devanagari and Hinglish tokenization, transliteration, and technical expansion |
| **Data & Graph Store** | **NumPy (`.npy`) & JSON Structured DB** | High-speed vector caching and relational normative graph stores |
| **Evaluation Suite** | **Custom Benchmark Engine (`eval_script.py`)** | Automated evaluation calculating Hit Rate@3, Hit Rate@5, MRR@5, and Latency |

---

## 📊 Evaluation & Benchmark Performance

Tested against the official benchmark evaluation dataset (`public_test_set.json`):

```
========================================
   BIS HACKATHON EVALUATION RESULTS
========================================
Total Queries Evaluated : 10
Hit Rate @3             : 100.00% 	(Target: >80%)
MRR @5                  : 1.0000 	(Target: >0.7)
Avg Latency             : 0.02 sec 	(Target: <5 seconds)
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
  1. Hybrid Search Architecture & BM25-Semantic Fusion.
  2. Standards Lifecycle & Currency Tracking Engine.
  3. Normative Reference & Testing Dependency Graph.
  4. Structured Technical Parameter Extraction Engine.
  5. Quality Control Order (QCO) Regulatory Framework.
  6. Indic / Vernacular / Multilingual Query Normalizer.
  7. Comparative Scope Disambiguation Matrix.
  8. CPWD/PWD Tender Specification & QA Checklist Generator.
  9. Interactive Streamlit Web Application & Benchmark Suite.

---

## 🚀 Quick Start & Usage

### 1. Installation
```bash
# Clone the repository
git clone <repository-url>
cd BIS-Standard-RE-master

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Interactive Web Dashboard
```bash
streamlit run interface.py
```

### 3. Run Automated Capability Verification Suite
Runs test assertions across all 6 core procedures:
```bash
python test_all_features.py
```

### 4. Run Batch Inference & Benchmark Evaluation
```bash
# Run batch inference
python inference.py --input public_test_set.json --output results.json

# Calculate evaluation metrics
python eval_script.py --results results.json
```

---

## 📁 Repository Structure

```
BIS-Standard-RE/
├── data/
│   ├── processed_data.json      # Indexed BIS standards documentation
│   ├── embeddings.npy           # Precomputed semantic vector embeddings
│   ├── standards_registry.json  # Lifecycle currency & revision registry
│   ├── normative_graph.json     # Test standards & allied code dependency graph
│   ├── parameters_db.json       # Quantitative physical & chemical parameters
│   ├── qco_compliance.json      # Government QCO orders & mandatory ISI database
│   └── vernacular_lexicon.json  # Hindi & Hinglish vernacular construction terms
├── src/
│   ├── retriever.py             # Hybrid search engine (BM25 + Semantic)
│   ├── pipeline.py              # Master pipeline orchestrator
│   ├── currency_manager.py      # Version control & currency manager
│   ├── normative_tracker.py     # Normative dependency resolver
│   ├── parameter_extractor.py   # Technical parameter extractor
│   ├── compliance_checker.py    # QCO regulatory inspector
│   ├── vernacular_normalizer.py # Multilingual & Indic NLP normalizer
│   ├── scope_comparator.py      # Comparative differentiation engine
│   ├── tender_generator.py      # Tender specification & QA checklist generator
│   └── llm_classifier.py        # Local Ollama query guardrail
├── test_all_features.py         # Automated verification suite (8 tests)
├── eval_script.py               # Benchmark evaluation script
├── inference.py                 # CLI batch inference script
├── interface.py                 # Interactive Streamlit Web Application
├── public_test_set.json         # Benchmark evaluation dataset
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```
