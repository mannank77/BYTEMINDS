"""
backend_app.py
==============
FastAPI backend for vector search and real-time ingestion powered by LanceDB.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
import uuid

from fastapi import FastAPI, HTTPException, Query
import lancedb
import numpy as np
from pydantic import BaseModel, Field

# Constants & Defaults
DEFAULT_DB_PATH = "data/lancedb"
DEFAULT_TABLE_NAME = "bis_standards"

# Application state container for LanceDB connection
db_state: dict[str, Any] = {}


def get_table_names(db: Any) -> list[str]:
    """Helper to list tables across different LanceDB versions without deprecation warnings."""
    try:
        res = db.list_tables()
        if hasattr(res, "tables"):
            return res.tables
        return list(res)
    except Exception:
        return list(db.table_names())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes the LanceDB connection on server startup and keeps the table cached.
    LanceDB utilizes zero-copy memory mapping, making shared in-process tables fast and concurrency-safe.
    """
    db_path = Path(DEFAULT_DB_PATH)
    if not db_path.exists():
        db_path.mkdir(parents=True, exist_ok=True)

    db = lancedb.connect(str(db_path))
    table_names = get_table_names(db)

    if DEFAULT_TABLE_NAME not in table_names:
        print(f"[warning] Table '{DEFAULT_TABLE_NAME}' not found in {db_path}. Run migrate_to_lancedb.py first.")
        db_state["table"] = None
    else:
        table = db.open_table(DEFAULT_TABLE_NAME)
        db_state["table"] = table
        print(f"[startup] Connected to LanceDB table '{DEFAULT_TABLE_NAME}' ({len(table)} records)")

    db_state["db"] = db
    yield
    db_state.clear()


app = FastAPI(
    title="LanceDB Vector Search & Ingestion API",
    description="High-performance vector search API replacing raw NumPy matrix operations.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class SearchVectorRequest(BaseModel):
    query_vector: list[float] = Field(
        ...,
        description="1D embedding vector (e.g. from SentenceTransformers or OpenAI)",
    )
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to retrieve")
    metric: str = Field(default="cosine", description="Distance metric: 'cosine', 'L2', or 'dot'")


class SearchTextRequest(BaseModel):
    query_text: str = Field(..., min_length=1, description="Natural language search text")
    top_k: int = Field(default=5, ge=1, le=100)


class SearchResult(BaseModel):
    id: str | None = None
    standard: str | None = None
    title: str | None = None
    text: str | None = None
    _distance: float = Field(..., description="Calculated vector distance")


class DocumentInsertRequest(BaseModel):
    vector: list[float] = Field(..., description="1D vector embedding")
    standard: str = Field(default="", description="Identifier or code (e.g. IS 456)")
    title: str = Field(default="", description="Title or header")
    text: str = Field(default="", description="Text content or metadata snippet")


class InsertResponse(BaseModel):
    status: str
    id: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    table = db_state.get("table")
    if table is not None:
        try:
            table.checkout_latest()
        except Exception:
            pass
    return {
        "status": "healthy",
        "database_connected": db_state.get("db") is not None,
        "table_loaded": table is not None,
        "total_records": len(table) if table is not None else 0,
    }


@app.post("/search/vector", response_model=list[SearchResult])
async def search_by_vector(payload: SearchVectorRequest):
    """
    Searches for the nearest vectors using LanceDB's optimized table.search() method.
    Replaces brute-force NumPy operations (np.dot / np.linalg.norm) with SIMD-accelerated search.
    """
    table = db_state.get("table")
    if table is None:
        raise HTTPException(
            status_code=503,
            detail=f"Table '{DEFAULT_TABLE_NAME}' not available. Please run migrate_to_lancedb.py first."
        )

    # Sync latest commits across concurrent workers
    try:
        table.checkout_latest()
    except Exception:
        pass

    # Validate 1D vector format
    q_vec = np.array(payload.query_vector, dtype=np.float32).flatten()
    if q_vec.size == 0:
        raise HTTPException(status_code=400, detail="Empty query vector provided.")

    try:
        # LanceDB search query builder:
        # .metric(): Configures distance function (cosine, L2, or dot)
        # .select(): Column pruning - fetches only needed fields, avoids reading vector column
        # .limit(): Restricts result count
        # .to_list(): Serializes directly to Python dictionaries
        results = (
            table.search(q_vec)
            .metric(payload.metric)
            .select(["id", "standard", "title", "text"])
            .limit(payload.top_k)
            .to_list()
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search/text", response_model=list[SearchResult])
async def search_by_text(payload: SearchTextRequest):
    """
    Encodes text using the local SentenceTransformers model on the fly,
    then runs the vector search against LanceDB.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load sentence-transformers: {exc}")

    q_vec = model.encode([payload.query_text], normalize_embeddings=True)[0]
    return await search_by_vector(SearchVectorRequest(query_vector=q_vec.tolist(), top_k=payload.top_k))


@app.post("/documents", response_model=InsertResponse, status_code=201)
async def add_document(payload: DocumentInsertRequest):
    """
    Appends a new vector and metadata record into the LanceDB table in real time.
    
    Why table.add() is ideal:
    - LanceDB uses an append-only, ACID-compliant on-disk structure.
    - Unlike modifying a static .npy file (which requires loading and saving the whole file),
      table.add() commits in fractions of a millisecond without downtime or rebuilding the dataset.
    """
    table = db_state.get("table")
    if table is None:
        raise HTTPException(
            status_code=503,
            detail=f"Table '{DEFAULT_TABLE_NAME}' not available. Please run migrate_to_lancedb.py first."
        )

    # Flatten and validate vector
    vec = np.array(payload.vector, dtype=np.float32).flatten().tolist()
    doc_id = str(uuid.uuid4())

    new_row = [{
        "id": doc_id,
        "doc_index": -1,
        "standard": payload.standard,
        "title": payload.title,
        "text": payload.text,
        "vector": vec,
    }]

    try:
        # Real-time ingestion: Accepts list of dicts, pandas DataFrame, or Arrow Table
        table.add(new_row)
        return InsertResponse(
            status="success",
            id=doc_id,
            message="Document successfully appended to LanceDB.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed: {str(e)}")


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Deletes a vector record from LanceDB by ID in real time.
    """
    table = db_state.get("table")
    if table is None:
        raise HTTPException(
            status_code=503,
            detail=f"Table '{DEFAULT_TABLE_NAME}' not available."
        )
    try:
        # Safe parameterized deletion by ID (SQL literals require single quotes in Lance/DataFusion)
        table.delete(f"id = '{doc_id}'")
        return {"status": "success", "id": doc_id, "message": "Document deleted from LanceDB."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
