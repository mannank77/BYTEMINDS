"""
migrate_to_lancedb.py
=====================
One-time execution script to migrate vector embeddings from .npy (e.g. data/embeddings.npy or data.npy)
into a high-performance local LanceDB table.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import uuid
import numpy as np
import pandas as pd
import lancedb


# Default paths relative to project root
DEFAULT_NUMPY_PATH = "data/embeddings.npy"
DEFAULT_METADATA_PATH = "data/processed_data.json"
DEFAULT_DB_PATH = "data/lancedb"
DEFAULT_TABLE_NAME = "bis_standards"


def load_embeddings(file_path: str | Path) -> np.ndarray:
    """Loads and validates vectors from a .npy file."""
    path = Path(file_path)
    if not path.exists():
        # Fallback to data.npy if requested file does not exist
        fallback = Path("data.npy")
        if fallback.exists():
            path = fallback
        else:
            raise FileNotFoundError(f"Embedding file not found: {file_path}")

    embeddings = np.load(str(path))
    if embeddings.ndim != 2:
        raise ValueError(
            f"Expected a 2D matrix of shape (N, D), but got {embeddings.shape}"
        )

    print(f"[migration] Loaded {embeddings.shape[0]} vectors with dimension {embeddings.shape[1]} from {path}")
    return embeddings.astype(np.float32)


def load_metadata(file_path: str | Path, num_records: int) -> list[dict]:
    """Loads metadata JSON or generates sensible default records."""
    path = Path(file_path)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) == num_records:
                print(f"[migration] Loaded {len(data)} metadata records from {path}")
                return data
            else:
                print(f"[migration] Metadata count ({len(data) if isinstance(data, list) else 0}) != vector count ({num_records}). Using partial/fallback metadata.")
        except Exception as e:
            print(f"[migration] Warning reading metadata: {e}. Generating fallback metadata.")

    # Fallback placeholder metadata
    return [{"standard": f"ITEM-{i+1}", "title": f"Document Record #{i+1}", "text": ""} for i in range(num_records)]


def migrate_to_lancedb(
    embeddings: np.ndarray,
    metadata: list[dict],
    db_path: str = DEFAULT_DB_PATH,
    table_name: str = DEFAULT_TABLE_NAME,
    metric: str = "cosine",
) -> lancedb.table.Table:
    """
    Ingests embeddings and metadata into a local LanceDB table.

    Why Pandas conversion is used:
    1. LanceDB natively ingests Pandas DataFrames through PyArrow zero-copy IPC buffers.
    2. Passing a 1D NumPy array or list-of-floats in the 'vector' column of a DataFrame
       allows LanceDB to infer the Apache Arrow FixedSizeList<float32> vector schema automatically,
       avoiding brittle manual PyArrow schema declarations.
    3. It cleanly packages tabular metadata (IDs, titles, text) alongside dense vectors.
    """
    db_dir = Path(db_path)
    db_dir.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(db_dir))

    num_records = len(embeddings)
    records = []

    for i in range(num_records):
        meta = metadata[i] if i < len(metadata) else {}
        records.append({
            "id": meta.get("id") or str(uuid.uuid4()),
            "doc_index": i,
            "standard": meta.get("standard", f"STD-{i}"),
            "title": meta.get("title", ""),
            "text": meta.get("text", "")[:1024],  # Store primary text chunk
            "vector": embeddings[i].tolist(),     # 1D vector (list of floats)
        })

    df = pd.DataFrame(records)

    # Ingest into LanceDB (mode="overwrite" guarantees idempotent re-runs)
    table = db.create_table(table_name, data=df, mode="overwrite")
    print(f"[migration] Successfully written {len(table)} rows to LanceDB table '{table_name}' at {db_path}")

    # Build ANN vector index for large datasets (if >= 256 records)
    if num_records >= 256:
        try:
            try:
                from lancedb.index import IvfPq
                table.create_index("vector", config=IvfPq(distance_type=metric))
            except Exception:
                table.create_index(metric=metric, vector_column_name="vector")
            print(f"[migration] Created '{metric}' index on 'vector' column.")
        except Exception as exc:
            print(f"[migration] Note: Flat scan used (index skipped: {exc})")

    return table


def main():
    parser = argparse.ArgumentParser(description="Migrate NumPy vectors to LanceDB.")
    parser.add_argument("--numpy-path", default=DEFAULT_NUMPY_PATH, help="Path to .npy vector file")
    parser.add_argument("--metadata-path", default=DEFAULT_METADATA_PATH, help="Path to metadata JSON")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="LanceDB database folder")
    parser.add_argument("--table-name", default=DEFAULT_TABLE_NAME, help="LanceDB table name")
    args = parser.parse_args()

    embeddings = load_embeddings(args.numpy_path)
    metadata = load_metadata(args.metadata_path, len(embeddings))
    table = migrate_to_lancedb(embeddings, metadata, args.db_path, args.table_name)

    # Quick sanity test search
    query_vector = embeddings[0]
    sample_res = (
        table.search(query_vector)
        .metric("cosine")
        .select(["id", "standard", "title", "_distance"])
        .limit(3)
        .to_list()
    )
    print("\n[migration] Sanity Check - Top 3 Nearest Neighbors to first vector:")
    for rank, res in enumerate(sample_res, 1):
        print(f"  {rank}. [{res.get('standard')}] {res.get('title')} (distance: {res.get('_distance'):.4f})")


if __name__ == "__main__":
    main()
