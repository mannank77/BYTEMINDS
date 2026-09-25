"""
scripts/reindex.py
Zero-downtime atomic reindexing script for Elasticsearch.
Creates a new target index version, bulk-indexes all standards,
and atomically swaps the 'bis_standards_active' alias.
"""
import json
import re
from pathlib import Path
import numpy as np
from elasticsearch import Elasticsearch, helpers

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed_data.json"
CACHE_PATH = ROOT / "data" / "embeddings.npy"
MAPPING_PATH = ROOT / "config" / "es_mapping.json"

ES_HOST = "http://localhost:9200"
ALIAS_NAME = "bis_standards_active"


def get_next_index_name(es: Elasticsearch) -> tuple[str, str | None]:
    """Find current index behind alias and determine next version name."""
    current_index = None
    if es.indices.exists_alias(name=ALIAS_NAME):
        indices = list(es.indices.get_alias(name=ALIAS_NAME).keys())
        if indices:
            current_index = indices[0]

    if current_index and re.search(r"_v(\d+)$", current_index):
        v = int(re.search(r"_v(\d+)$", current_index).group(1))
        next_index = f"bis_standards_v{v + 1}"
    else:
        next_index = "bis_standards_v2" if current_index == "bis_standards_v1" else "bis_standards_v1"

    return next_index, current_index


def reindex():
    print(f"Connecting to Elasticsearch at {ES_HOST} ...")
    es = Elasticsearch(ES_HOST)
    if not es.ping():
        raise ConnectionError(f"Could not connect to Elasticsearch at {ES_HOST}. Is Docker running?")

    next_index, current_index = get_next_index_name(es)
    print(f"Current active index: {current_index}")
    print(f"Creating new target index: {next_index} ...")

    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    if es.indices.exists(index=next_index):
        print(f"Index {next_index} already exists. Deleting it ...")
        es.indices.delete(index=next_index)

    es.indices.create(index=next_index, body=mapping)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    embeddings = np.load(str(CACHE_PATH))
    print(f"Bulk-indexing {len(documents)} documents into {next_index} ...")

    actions = [
        {
            "_index": next_index,
            "_id": str(i),
            "_source": {
                "standard": doc.get("standard", ""),
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
                "text": doc.get("text", "")[:1500],
                "embedding": embeddings[i].tolist(),
            },
        }
        for i, doc in enumerate(documents)
    ]

    success, failed = helpers.bulk(es, actions)
    print(f"Bulk indexing into {next_index} complete! Indexed: {success} (Failed: {len(failed) if isinstance(failed, list) else 0})")

    # Atomic alias swap
    alias_actions = []
    if current_index:
        alias_actions.append({"remove": {"index": current_index, "alias": ALIAS_NAME}})
    alias_actions.append({"add": {"index": next_index, "alias": ALIAS_NAME}})

    print(f"Performing atomic alias swap for '{ALIAS_NAME}' ...")
    es.indices.update_aliases(body={"actions": alias_actions})
    print(f"SUCCESS: '{ALIAS_NAME}' now points to '{next_index}' with zero downtime!")


if __name__ == "__main__":
    reindex()
