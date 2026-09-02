import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.checkpoint import get_sqlite_checkpointer
from agent.graph import build_graph
from tools.order_tool import check_order_status

# Initialize FastAPI App
app = FastAPI(
    title="Nykaa Support Agent API",
    description="REST API for RAG, Order Tracking, and Agent Checkpointing.",
    version="1.0.0",
)

# Initialize Checkpointer and LangGraph Application
checkpointer = get_sqlite_checkpointer()
agent_app = build_graph(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    thread_id: str
    query: str


class ChatResponse(BaseModel):
    thread_id: str
    query: str
    route: str
    final_response: str


class OrderStatusResponse(BaseModel):
    record_id: str
    status: str
    order_value_inr: float
    escalation_score: float
    escalation_recommended: bool


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Health check endpoint to verify API readiness."""
    return {"status": "ok", "service": "Nykaa Support Agent API"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Submits a user query to the LangGraph support agent."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    config = {"configurable": {"thread_id": request.thread_id}}
    input_data = {
        "thread_id": request.thread_id,
        "query": request.query.strip()
    }

    try:
        result = agent_app.invoke(input_data, config=config)
        return ChatResponse(
            thread_id=request.thread_id,
            query=request.query,
            route=result.get("route", "unknown"),
            final_response=result.get("final_response", "No response generated.")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/order/{order_id}", response_model=OrderStatusResponse)
def get_order_status(order_id: str):
    """Direct lookup endpoint for order details via FastMCP tool."""
    try:
        details = check_order_status(order_id.upper())
        if "error" in details:
            raise HTTPException(status_code=404, detail=details["error"])
        return details
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))