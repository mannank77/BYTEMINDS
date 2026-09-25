# 🛠️ Elasticsearch Setup & Operations Guide (Person 1)

> **Document Scope:** Setup, ingestion, health verification, and maintenance of the Elasticsearch 8.x cluster.

---

## 1. Quick Start

### Step 1: Start Elasticsearch
Run from the repository root:
```bash
docker compose up -d
```
* The cluster runs in the background at `http://localhost:9200`.
* Configured with 1 GB heap limit (`-Xms1g -Xmx1g`) and persistent volume `es_data`.

### Step 2: Index All Standards (Ingestion)
Run the bulk indexing script:
```bash
python scripts/index_elasticsearch.py
```
* Loads `data/processed_data.json` (565 standards).
* Attaches 384-dimensional dense vectors from `data/embeddings.npy`.
* Creates index `bis_standards_v1` using `config/es_mapping.json`.
* Points the active alias `bis_standards_active` to `bis_standards_v1`.

### Step 3: Verify Health
Run the automated healthcheck:
```bash
python scripts/es_healthcheck.py
```
Expected output:
```text
 SUCCESS: Elasticsearch cluster is ONLINE!
 Cluster Name : docker-cluster
 ES Version   : 8.14.3
 Active Alias : 'bis_standards_active' -> 565 documents indexed
```

---

## 2. Common Maintenance Commands

| Action | Command |
| :--- | :--- |
| **Start Cluster** | `docker compose up -d` |
| **Stop Cluster** | `docker compose down` |
| **Check Logs** | `docker compose logs -f` |
| **Check Cluster Health (cURL)** | `curl http://localhost:9200/_cluster/health?pretty` |
| **Inspect Active Index** | `curl http://localhost:9200/bis_standards_active/_count` |
| **Reset / Reindex Data** | `python scripts/index_elasticsearch.py` |

---

## 3. Python Compatibility Note

The Elasticsearch Python client version must match Elasticsearch 8.x:
```bash
pip install "elasticsearch>=8.14.0,<9.0.0"
```
*(Do not install `elasticsearch>=9.0.0`, as version 9 sends headers incompatible with ES 8.x clusters).*
