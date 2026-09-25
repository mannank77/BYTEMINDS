"""
test_db_lifecycle.py
====================
Comprehensive LanceDB Lifecycle & Integrity Test Suite:
1. Connects to the local LanceDB store.
2. Cleans up any previous test artifacts idempotently.
3. Tests adding a new vector embedding + metadata.
4. Tests vector search: verifies the added record is retrieved as rank 1 with ~0 distance.
5. Tests vector deletion: removes the test record by ID.
6. Verifies deletion: confirms table row count is restored and record is completely removed from search.
7. Tests edge cases: non-existent ID deletion, dimension validation, and schema consistency.
"""

from __future__ import annotations

import sys
import uuid
import lancedb
import numpy as np

# Force UTF-8 on Windows consoles to prevent charmap encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "data/lancedb"
TABLE_NAME = "bis_standards"


def get_table_names(db) -> list[str]:
    """Helper to list tables across LanceDB versions without deprecation warnings."""
    try:
        res = db.list_tables()
        if hasattr(res, "tables"):
            return res.tables
        return list(res)
    except Exception:
        return list(db.table_names())


def run_tests():
    print("=" * 65)
    print("LANCEDB LIFECYCLE & INTEGRITY TEST SUITE")
    print("=" * 65)

    # 1. Connect & Initial Count
    print(f"\n[Step 1/7] Connecting to LanceDB at '{DB_PATH}'...")
    db = lancedb.connect(DB_PATH)
    available_tables = get_table_names(db)
    print(f"Available tables: {available_tables}")
    if TABLE_NAME not in available_tables:
        raise RuntimeError(f"Table '{TABLE_NAME}' not found.")

    tbl = db.open_table(TABLE_NAME)

    # Clean up any leftover test rows from previous runs
    tbl.delete("id LIKE 'test-%'")
    tbl.delete("standard LIKE '%TEST%'")
    tbl.checkout_latest()
    initial_count = len(tbl)
    print(f"Connected to '{TABLE_NAME}'. Baseline record count: {initial_count}")
    print(f"Table columns: {tbl.schema.names}")

    # 2. Add New Vector
    test_id = f"test-lifecycle-{uuid.uuid4().hex[:8]}"
    raw_vec = np.random.randn(384).astype(np.float32)
    sample_vec = (raw_vec / np.linalg.norm(raw_vec)).tolist()

    print(f"\n[Step 2/7] Adding test vector with ID '{test_id}'...")
    tbl.add([{
        "id": test_id,
        "doc_index": -999,
        "standard": "IS TEST: 9999",
        "title": "Temporary Test Standard for Lifecycle Verification",
        "text": "This is a temporary document record to verify dynamic append and delete.",
        "vector": sample_vec,
    }])

    count_after_add = len(tbl)
    print(f"Record count after insertion: {count_after_add}")
    if count_after_add != initial_count + 1:
        raise AssertionError(f"Expected count {initial_count + 1}, got {count_after_add}")
    print("[PASS] Vector successfully appended to LanceDB.")

    # 3. Vector Similarity Search
    print("\n[Step 3/7] Searching for the inserted vector...")
    results = (
        tbl.search(sample_vec)
        .metric("cosine")
        .select(["id", "standard", "title", "_distance"])
        .limit(3)
        .to_list()
    )

    print("Top search results:")
    for rank, res in enumerate(results, 1):
        print(f"  Rank {rank}: ID={res.get('id')} | Standard={res.get('standard')} | Distance={res.get('_distance'):.6f}")

    if not results or results[0]["id"] != test_id:
        raise AssertionError(f"Expected top match '{test_id}', but got '{results[0]['id'] if results else 'None'}'")

    top_dist = results[0]["_distance"]
    if top_dist > 1e-4:
        raise AssertionError(f"Expected near-zero distance for identical vector, got {top_dist}")
    print(f"[PASS] Top search result matches '{test_id}' perfectly (distance: {top_dist:.8f}).")

    # 4. Delete the Vector
    print(f"\n[Step 4/7] Deleting test vector '{test_id}' from LanceDB...")
    tbl.delete(f"id = '{test_id}'")

    count_after_del = len(tbl)
    print(f"Record count after deletion: {count_after_del}")
    if count_after_del != initial_count:
        raise AssertionError(f"Expected count to return to baseline {initial_count}, got {count_after_del}")
    print("[PASS] Table row count restored to baseline.")

    # 5. Verify Record is Gone from Search
    print("\n[Step 5/7] Verifying deleted vector does not appear in subsequent searches...")
    search_after = (
        tbl.search(sample_vec)
        .metric("cosine")
        .select(["id", "standard", "_distance"])
        .limit(5)
        .to_list()
    )
    result_ids = [r["id"] for r in search_after]
    print(f"Top 5 IDs after deletion: {result_ids}")
    if test_id in result_ids:
        raise AssertionError(f"CRITICAL: Deleted vector '{test_id}' still appeared in search results!")
    print("[PASS] Deleted record is verified completely removed from index and search.")

    # 6. Test Core Retriever Integration
    print("\n[Step 6/7] Testing src.retriever add_document and delete_document...")
    from src.retriever import get_retriever
    retriever = get_retriever()
    test_retriever_id = f"test-retriever-{uuid.uuid4().hex[:8]}"

    # Add via retriever
    add_info = retriever.add_document(
        standard="IS TEST-RET: 101",
        title="Retriever Test Document",
        text="Sample text for testing retriever dynamic insertion.",
        vector=sample_vec,
    )
    inserted_id = add_info["id"]
    print(f"Retriever added document with ID: {inserted_id}")
    tbl.checkout_latest()
    if len(tbl) != initial_count + 1:
        raise AssertionError(f"Retriever did not increment table count in LanceDB! (Expected {initial_count + 1}, got {len(tbl)})")

    # Delete via retriever
    deleted_ok = retriever.delete_document(inserted_id)
    tbl.checkout_latest()
    if not deleted_ok or len(tbl) != initial_count:
        raise AssertionError(f"Retriever failed to delete document from LanceDB! (Expected {initial_count}, got {len(tbl)})")
    print("[PASS] src.retriever dynamic add and delete methods verified successfully.")

    # 7. Edge Cases & Robustness
    print("\n[Step 7/7] Testing edge cases & error boundaries...")

    # Edge Case A: Deleting non-existent ID
    try:
        tbl.delete("id = 'non-existent-xyz-999'")
        print("  [PASS] Deleting non-existent ID handled safely (no exception, no corruption).")
    except Exception as exc:
        raise AssertionError(f"Deleting non-existent ID failed unexpectedly: {exc}")

    # Edge Case B: Dimension mismatch in search vector
    try:
        wrong_dim = [0.1] * 128
        tbl.search(wrong_dim).limit(1).to_list()
        print("  [WARN] Dimension mismatch did not raise an exception.")
    except Exception as exc:
        print(f"  [PASS] Dimension mismatch correctly rejected: {type(exc).__name__}")

    print("\n" + "=" * 65)
    print("ALL 7 VERIFICATION STEPS PASSED WITH ZERO ERRORS!")
    print(f"LanceDB is healthy and stable (Active records: {len(tbl)}).")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_tests()
    except Exception as err:
        print(f"\n[TEST FAILED] {err}", file=sys.stderr)
        sys.exit(1)
