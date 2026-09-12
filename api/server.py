import json
import logging
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.checkpoint import get_sqlite_checkpointer
from agent.graph import build_graph
from agent.guardrails import mask_pii, detect_injection
from tools.order_tool import check_order_status

# --- IMPORT CHROMADB AND EMBEDDING MODEL ---
from rag.generator import collection, model as embedding_model  # Ensure your collection & model are imported here

# Setup file logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_DIR / "requests.jsonl")
logger.addHandler(handler)

app = FastAPI(title="Nykaa Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph(checkpointer=get_sqlite_checkpointer())


# --- SCHEMAS ---

class AskPayload(BaseModel):
    thread_id: str = Field(..., example="thread_001")
    query: str = Field(..., example="Where is ORD1001?")


class AddDocPayload(BaseModel):
    filename: str
    content: str


# --- GUARDRAIL DEPENDENCY ---

def validate_and_sanitize(payload: AskPayload) -> AskPayload:
    """Sanitize input queries and check for injection before processing."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if detect_injection(payload.query):
        raise HTTPException(
            status_code=400, 
            detail="Query flagged by security filters."
        )

    payload.query = mask_pii(payload.query)
    return payload


# --- ROUTES ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask_agent(payload: Annotated[AskPayload, Depends(validate_and_sanitize)]):
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    res = graph.invoke(
        {"thread_id": payload.thread_id, "query": payload.query},
        config=config
    )

    out = {
        "thread_id": payload.thread_id,
        "query": payload.query,
        "route": res.get("route", "rag"),
        "final_response": res.get("final_response", ""),
        "response": res.get("final_response", "")
    }

    logger.info(json.dumps(out))
    return out


@app.get("/order/{order_id}")
def get_order(order_id: str):
    res = check_order_status(order_id.upper())
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@app.post("/add-document")
def upload_doc(payload: AddDocPayload):
    try:
        # 1. Save file locally
        target = Path("data/knowledge_base") / Path(payload.filename).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload.content, encoding="utf-8")

        # 2. Extract Document ID
        doc_id = payload.filename.split("_")[0] if "_" in payload.filename else "KB011"

        # 3. Clean and split paragraphs cleanly (filtering out short fragments)
        raw_paragraphs = payload.content.split("\n\n")
        chunks = []
        for p in raw_paragraphs:
            cleaned = p.strip()
            # Only keep chunks longer than 20 characters to avoid trailing fragments
            if len(cleaned) > 20:
                chunks.append(f"Document ID: {doc_id}\nTopic: {payload.filename}\n\n{cleaned}")

        if not chunks:
            chunks = [f"Document ID: {doc_id}\nTopic: {payload.filename}\n\n{payload.content.strip()}"]

        # 4. Generate normalized embeddings
        embeddings = embedding_model.encode(chunks, normalize_embeddings=True).tolist()

        # 5. Build IDs and metadata
        ids = [f"{payload.filename}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"document_id": doc_id, "source": payload.filename}] * len(chunks)

        # 6. Upsert into Chroma collection
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        return {"status": "created", "path": str(target), "indexed_chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))