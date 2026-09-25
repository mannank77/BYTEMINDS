"""
scripts/index_elasticsearch.py
Reads processed_data.json and precomputed embeddings, then bulk-indexes
all standards into Elasticsearch with an alias 'bis_standards_active'.
"""
import json
from pathlib import Path
import numpy as np
from elasticsearch import Elasticsearch, helpers

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed_data.json"
CACHE_PATH = ROOT / "data" / "embeddings.npy"
MAPPING_PATH = ROOT / "config" / "es_mapping.json"

ES_HOST = "http://localhost:9200"
INDEX_NAME = "bis_standards_v1"
ALIAS_NAME = "bis_standards_active"


def main():
    print(f"Connecting to Elasticsearch at {ES_HOST} ...")
    es = Elasticsearch(ES_HOST)
    if not es.ping():
        raise ConnectionError(f"Could not connect to Elasticsearch at {ES_HOST}. Is Docker running?")

    # 1. Load mapping
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # 2. Re-create index if already exists
    if es.indices.exists(index=INDEX_NAME):
        print(f"Deleting existing index: {INDEX_NAME} ...")
        es.indices.delete(index=INDEX_NAME)

    print(f"Creating index '{INDEX_NAME}' with custom analyzers & vector mappings ...")
    es.indices.create(index=INDEX_NAME, body=mapping)

    # 3. Load documents and precomputed embeddings
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    if not CACHE_PATH.exists():
        raise FileNotFoundError(f"Embedding file not found at {CACHE_PATH}. Run inference once to create it.")

    embeddings = np.load(str(CACHE_PATH))
    print(f"Loaded {len(documents)} documents and {len(embeddings)} precomputed vectors.")

    # 4. Prepare bulk actions
    actions = []
    for i, doc in enumerate(documents):
        action = {
            "_index": INDEX_NAME,
            "_id": str(i),
            "_source": {
                "standard": doc.get("standard", ""),
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "text": doc.get("text", "")[:1500],
                "embedding": embeddings[i].tolist(),
            },
        }
        actions.append(action)

    print(f"Streaming {len(actions)} documents to Elasticsearch ...")
    success, failed = helpers.bulk(es, actions)
    print(f"Bulk ingestion complete! Successfully indexed: {success} (Failed: {len(failed) if isinstance(failed, list) else 0})")

    # 5. Point alias 'bis_standards_active' to 'bis_standards_v1'
    es.indices.put_alias(index=INDEX_NAME, name=ALIAS_NAME)
    print(f"Alias '{ALIAS_NAME}' linked to '{INDEX_NAME}'.")
    print("Done! Person 2 can now query Elasticsearch.")


if __name__ == "__main__":
    main()
