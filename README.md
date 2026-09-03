# Nykaa Support Agent

An E-Commerce customer support assistant designed for policy retrieval, order tracking, and escalation management. Built with LangGraph, FastAPI, Streamlit, and ChromaDB.

---

## Technical Features

* **LangGraph Orchestration:** Stateful graph navigation, multi-node execution, and conditional routing between RAG and transactional order tools.
* **Retrieval-Augmented Generation:** ChromaDB vector similarity search over Nykaa store policy documentation and FAQs.
* **Order Tracking Operations:** Order status lookup, value retrieval, and automated escalation scoring via FastMCP integration.
* **Session Persistence:** State saving and thread isolation powered by SQLite (`SqliteSaver`).
* **API Layer:** FastAPI service with Pydantic schema validation, error handling, and Swagger documentation.
* **Web Dashboard:** Streamlit interface for live interactive chat, thread switching, and quick order lookups.
* **Guardrails & Evaluation:** Input sanitization, PII masking, prompt injection checking, and RAG Triad quality metrics.

---

## Directory Structure

```text
nykaa-support-agent/
├── agent/                  # Graph definition, nodes, schemas, and guardrails
│   ├── checkpoint.py       # SQLite persistence setup
│   ├── escalation.py       # Human-in-the-loop (HITL) module
│   ├── graph.py            # State graph workflow definition
│   ├── guardrails.py       # PII redaction and input security
│   └── schema.py           # Pydantic graph state schemas
├── api/                    # FastAPI service layer
│   └── app.py              # Controller endpoints (/chat, /order/{id}, /health)
├── chroma_data/            # Vector database storage
├── data/                   # Mock storage and runtime persistence
│   ├── checkpoints.db      # SQLite checkpoint database
│   └── orders.json         # Mock order database
├── memory/                 # Session history handlers
├── rag/                    # Embeddings and document retriever modules
├── tools/                  # Tool abstractions and external handlers
│   └── order_tool.py       # Order tracking implementation
├── ui/                     # User interface source code
│   └── app.py              # Streamlit client app
├── dataset.py              # Evaluation benchmark datasets
├── mcp_client.py           # MCP client testing
├── mcp_server.py           # MCP server initialization
├── requirements.txt        # Dependencies
└── README.md

Getting Started
1. Environment Setup
Initialize and activate a Python virtual environment:

python -m venv .venv
Activate environment:


# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
Install dependencies:


pip install -r requirements.txt
2. Running Services
Run both backend and frontend processes simultaneously in separate terminal windows.

Terminal 1: FastAPI Backend
uvicorn api.app:app --reload --port 8001
API Documentation: http://127.0.0.1:8001/docs

Health Check: http://127.0.0.1:8001/health

Terminal 2: Streamlit Dashboard

streamlit run app.py
Web Dashboard: http://127.0.0.1:8501

System Verification
Run tests to verify subsystem functionality:

Checkpoints:


python -m agent.checkpoint
Human Interruption & Resume:


python -m agent.escalation
RAG Triad Metrics:

python -m rag.evaluate_triad