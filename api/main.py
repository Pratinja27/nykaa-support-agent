import json
import time
import os
import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.graph import build_graph
from agent.guardrails import mask_pii, detect_injection
from agent.schema import AgentResponseSchema

app = FastAPI(title="Nykaa Support Agent API", version="1.0")

graph_app = build_graph()

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "requests.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)


class AskRequest(BaseModel):
    thread_id: str = Field(..., example="thread_001")
    query: str = Field(..., example="What is the status of ORD1001?")


class AddDocumentRequest(BaseModel):
    filename: str = Field(..., example="policies/returns.txt")
    content: str = Field(..., example="Nykaa return policy allows returns within 15 days.")


def log_request_jsonl(log_data: Dict[str, Any]) -> None:
    """Task 12: Appends structured log entry to logs/requests.jsonl."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data) + "\n")


@app.post("/ask", response_model=AgentResponseSchema)
def ask_agent(req: AskRequest):
    """Task 11: Main query endpoint with Task 10 guardrails and Task 9 schema."""
    start_time = time.time()
    trace_id = str(uuid.uuid4())

    if detect_injection(req.query):
        raise HTTPException(
            status_code=400, 
            detail="Security Policy Violation: Prompt injection attempt detected."
        )

    masked_query = mask_pii(req.query)

    graph_input = {"thread_id": req.thread_id, "query": masked_query}
    graph_output = graph_app.invoke(graph_input)

    duration = round(time.time() - start_time, 4)

    response_obj = AgentResponseSchema(
        thread_id=req.thread_id,
        query=masked_query,
        route=graph_output.get("route", "rag"),
        final_response=graph_output.get("final_response", "No response generated."),
        source=graph_output.get("source", "system"),
        metadata={"trace_id": trace_id}
    )

    log_entry = {
        "trace_id": trace_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_sec": duration,
        "thread_id": req.thread_id,
        "query_masked": masked_query,
        "route": response_obj.route,
        "final_response": response_obj.final_response
    }
    log_request_jsonl(log_entry)

    return response_obj


@app.post("/add-document")
def add_document(req: AddDocumentRequest):
    """Task 11: Dynamic document ingestion endpoint."""
    kb_path = os.path.join("data", "knowledge_base", os.path.basename(req.filename))
    os.makedirs(os.path.dirname(kb_path), exist_ok=True)

    with open(kb_path, "w", encoding="utf-8") as f:
        f.write(req.content)

    return {
        "status": "success",
        "message": f"Document '{req.filename}' added to knowledge base successfully."
    }