# Nykaa Support Agent

An E-Commerce customer support assistant designed for policy retrieval, order tracking, and escalation management. Built with LangGraph, FastAPI, Streamlit, and ChromaDB.

---

# Nykaa AI Support Agent (E-Commerce & Retail Track)

> **Track:** Nykaa (E-commerce & Retail)  
> **Mode:** Deterministic `MOCK_LLM` (Zero API keys required)

---

## 📌 Task 1: Order Dataset Design Choices

* **Random Seed:** `42`
* **Total Order Records Generated:** `50` (Requirement: ≥40)
* **Categories Count (All ≥3):**
  - Apparel: 5
  - Electronics: 5
  - Home: 14
  - Footwear: 13
  - Beauty: 13
* **Statuses Count (All ≥1):**
  - Placed: 12
  - Shipped: 17
  - Delivered: 9
  - Returned: 7
  - Refunded: 5
* **Delayed Shipment Rate:** `12.00%` (6/50) — calibrated strictly within the required 10.00%–30.00% range.
* **Order Amount Range:** ₹499 to ₹15,000

---

## 📌 Task 2: Knowledge Base Documents

The `knowledge_base/` directory contains 12 original Markdown documents covering all mandatory policy topics:

1. **Return Window by Category:** `knowledge_base/return_policy.md`
2. **COD Refund Timelines:** `knowledge_base/cod_refund.md`
3. **Delivery SLAs:** `knowledge_base/delivery_sla.md`
4. **Reverse-Pickup Eligibility:** `knowledge_base/reverse_pickup.md`
5. **Warranty Terms by Category:** `knowledge_base/warranty.md`
6. **Order Cancellation Policy:** `knowledge_base/cancellation.md`
7. **Loyalty Points Redemption:** `knowledge_base/loyalty_points.md`
8. **Payment Failure and Retry Policy:** `knowledge_base/payment_retry.md`
9. **Size Exchange Policy:** `knowledge_base/size_exchange.md`
10. **Damaged Item Claim Process:** `knowledge_base/damaged_item.md`
11. **International Shipping Restrictions:** `knowledge_base/international_shipping.md`
12. **Support Escalation Matrix:** `knowledge_base/escalation_matrix.md`

---

## 📌 Task 3: Knowledge Base Chunking & Vector Collections

Two distinct document chunking strategies were implemented and indexed into separate persistent ChromaDB collections (`chroma_data/`):

1. **Fixed-Size Chunking (`fixed_overlap` collection):**
   * **Strategy:** Fixed token/character window with overlap.
   * **Total Chunks Generated:** 35
2. **Sentence-Based Chunking (`sentence_based` collection):**
   * **Strategy:** Boundary splitting by sentence punctuation.
   * **Total Chunks Generated:** 24

Both strategies indexed all 12 knowledge base documents successfully into their respective ChromaDB collections.

---

## 📌 Task 4: Grounded Generation & Threshold Calibration

Empirical calibration was conducted using representative in-scope and out-of-scope test queries to establish a reliable retrieval threshold for grounded generation:

* **In-Scope Similarity Range:** `0.5191` to `0.8704`
* **Out-of-Scope Similarity Range:** `0.0739` to `0.1215`
* **Calibrated Threshold:** `0.35`

### Calibration Summary Data
| Query Type | Query | Top KB Match | Similarity Score |
| :--- | :--- | :--- | :--- |
| **In-Scope** | *What is the return window for footwear?* | `KB001` | **0.5191** |
| **In-Scope** | *How long does a COD refund take?* | `KB002` | **0.8704** |
| **In-Scope** | *Can I exchange my shoes for another size?* | `KB009` | **0.5721** |
| **In-Scope** | *How long does standard delivery take?* | `KB003` | **0.6370** |
| **Out-of-Scope** | *What is the capital of France?* | `KB011` | **0.1215** |
| **Out-of-Scope** | *Write a Python program to sort a list.* | `KB012` | **0.0739** |

Queries scoring below `0.35` automatically trigger the fallback refusal response (*"I don't have enough information in my knowledge base to answer this."*), preventing hallucinations.

---

## 📌 Task 5: RAG Evaluation & Chunking Recommendation

Precision@3 and Recall@3 were evaluated across 5 test queries for both vector collections:

### Retrieval Performance Comparison
| Metric | Fixed-Size Chunking (`nykaa_fixed_chunks`) | Sentence-Based Chunking (`nykaa_sentence_chunks`) |
| :--- | :--- | :--- |
| **Average Precision@3** | **0.467** | **0.433** |
| **Average Recall@3** | **1.000** | **1.000** |

### Per-Query Arithmetic Breakdown
1. **Query:** *What is the return window for footwear?* (Relevant: `KB001`)
   * **Fixed:** Retrieved [`KB001`, `KB009`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**
   * **Sentence:** Retrieved [`KB001`, `KB009`, `KB004`] | Precision@3 = 1/3 = **0.333** | Recall@3 = 1/1 = **1.000**
2. **Query:** *How long does a COD refund take?* (Relevant: `KB002`)
   * **Fixed:** Retrieved [`KB002`, `KB001`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**
   * **Sentence:** Retrieved [`KB002`, `KB006`, `KB001`] | Precision@3 = 1/3 = **0.333** | Recall@3 = 1/1 = **1.000**
3. **Query:** *How long does standard delivery take?* (Relevant: `KB003`)
   * **Fixed:** Retrieved [`KB003`, `KB001`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**
   * **Sentence:** Retrieved [`KB003`, `KB001`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**
4. **Query:** *Can I exchange my shoes for another size?* (Relevant: `KB009`)
   * **Fixed:** Retrieved [`KB009`, `KB004`, `KB010`] | Precision@3 = 1/3 = **0.333** | Recall@3 = 1/1 = **1.000**
   * **Sentence:** Retrieved [`KB009`, `KB001`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**
5. **Query:** *Can I cancel an order after it has shipped?* (Relevant: `KB006`)
   * **Fixed:** Retrieved [`KB006`, `KB008`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**
   * **Sentence:** Retrieved [`KB006`, `KB008`] | Precision@3 = 1/2 = **0.500** | Recall@3 = 1/1 = **1.000**

### Strategy Recommendation
**Recommendation:** We select **Fixed-Size Chunking** as the primary vector index for production deployment. Both approaches achieve a perfect Recall@3 of 1.000, but Fixed-Size Chunking delivers higher Precision@3 (**0.467** vs **0.433**), reducing irrelevant context injected into the agent prompt.

---

## 📌 Task 6: Order Status Tool & Escalation Logic

The order retrieval tool (`tools/order_tool.py`) queries order records directly from the database and evaluates customer distress via a deterministic scoring formula.

### Escalation Scoring Formula
$$\text{Escalation Score} = 0.6 \times \text{delayed\_signal} + 0.4 \times \left(\frac{\text{days\_since\_created}}{30}\right)$$

* **Escalation Threshold:** `0.75`

### Sample Output Demonstrations
* **High Escalation Case (`ORD1022`):**
  * Status: `Returned` | Score: **0.867** | Escalation Recommended: `True`
* **Low Escalation Case (`ORD1001`):**
  * Status: `Placed` | Score: **0.093** | Escalation Recommended: `False`

---

## 📌 Task 7: LangGraph Dynamic Architecture & State Routing

The support agent is built using a stateful LangGraph state machine with 4 distinct nodes and dynamic conditional edge routing:

* **Nodes:** `guardrail_node` $\rightarrow$ `intent_router` $\rightarrow$ `rag_node` / `order_tool_node` $\rightarrow$ `escalation_node`
* **Conditional Edge:** `route_intent` dynamically routes requests based on input query classification:
  - **Order Inquiries:** Routes to `order_tool_node` (SQL database lookup).
  - **Policy Inquiries:** Routes to `rag_node` (ChromaDB grounded vector search).

---

## 📌 Task 8: Multi-Turn Memory & State Persistence

State persistence is enabled via SQLite checkpointer threads, permitting context retention across multiple turns:

* **Thread State Continuity:** Initializing order context (`ORD1001`) allows follow-up questions like *"What is the status?"* to correctly resolve the implicit order context.
* **Thread Isolation:** Separate state checkpointer keys preserve distinct conversation sessions independently.

---

## 📌 Task 9 & Task 13: Automated E2E Pipeline & RAG Triad Evaluation

An automated evaluation harness (`rag/evaluate_triad.py`) was executed across 15 test scenarios (13 in-scope policy categories and 2 out-of-scope adversarial prompts). 

### Aggregate RAG Triad Metrics
| Evaluation Metric | Target Score | Achieved Mean Score |
| :--- | :--- | :--- |
| **Context Relevance** | > 0.70 | **0.787** |
| **Groundedness** | > 0.80 | **0.841** |
| **Answer Relevance** | > 0.70 | **0.774** |

### Sample Metric Breakdown Across Test Cases
* **In-Scope Queries (IDs 1–13):** Consistently achieved **0.89 Context Relevance**, **0.94 Groundedness**, and **0.87 Answer Relevance**.
* **Out-of-Scope Queries (IDs 14–15):** Triggered fallback refusals with low scores (**0.12 Context Relevance**, **0.20 Groundedness**), demonstrating strict guardrail boundaries.

---

## 📌 Task 10: Multi-Layer Guardrails System

Comprehensive guardrails run at both input and output stages of the agent pipeline (`agent/guardrails.py`):

### 1. Input Guardrails
* **PII Masking:** Uses regex and structural pattern matching to anonymize phone numbers (`[REDACTED_PHONE]`), credit cards (`[REDACTED_CARD]`), and emails prior to prompt construction.
* **Prompt Injection Defense:** Scans incoming user messages for instruction override patterns and context escape attempts (`Injected: True`).

### 2. Output Guardrails
* **Groundedness Verification:** Checks context retrieval scores against the calibrated threshold (`0.35`). Queries scoring below the threshold (e.g., score `0.18`) trigger an automatic fallback response (*"I am sorry, but I do not have enough verified information to answer this question accurately."*).

---

## 📌 Task 11: FastAPI Service Backend

The REST API layer (`api/app.py`) exposes production endpoints:

* **`POST /chat`:** Accepts thread ID and user queries, executes guardrails, routes requests through the LangGraph agent, and returns structured JSON responses.
* **`GET /order/{order_id}`:** Direct order status lookup via FastMCP integration.
* **`GET /health`:** API health check endpoint.

---

## 📌 Task 12: Structured Logging & Observability

All API interactions are intercepted and logged asynchronously to `logs/requests.jsonl` with full request metadata:

* **Logging Schema:** `trace_id`, `timestamp`, `duration_sec`, `thread_id`, `query_masked`, `route`, and `final_response`.
* **Traceability:** Every interaction receives a unique UUID `trace_id` for end-to-end debugging and latency tracking.

---

## 📌 Task 14: Streamlit User Interface

An interactive Streamlit front-end (`ui.py`) serves as the operational client interface:

* **Session & Memory Tracking:** Retains `thread_id` state across chat sessions via `st.session_state`.
* **Guardrail Interception:** Intercepts prompt injections and redacts sensitive PII before making API requests.
* **Route Metadata:** Displays real-time routing tags (`[Route: order_tool]` vs `[Route: rag]`) alongside agent responses.
* **Dynamic KB Ingestion:** Includes a sidebar panel allowing support admins to upload new policy documents directly to the knowledge base.

---

## 📌 Task 15: System Capabilities & Performance Matrix

| System Component | Capability / Feature | Operational Behavior / Mechanism | Benchmark / Verification Metric |
| :--- | :--- | :--- | :--- |
| **Document Ingestion** | Fixed & Sentence Chunking | Hybrid chunking pipeline (`rag/chunking.py`) targeting precision vs context balance. | Precision@3: **0.467** (Fixed) vs **0.433** (Sentence) |
| **Similarity Search** | Vector Indexing | ChromaDB integration (`rag/index.py`) using huggingface embeddings for fast similarity search. | Recall@3: **1.000** across test sets |
| **Query Calibration** | Groundedness Thresholding | Calibrated decision boundary (`rag/calibrate.py`) to minimize hallucinations. | Similarity Score Cutoff: **0.35** |
| **Order Tracking** | SQL Lookup & Escalation | FastMCP order tool (`tools/order_tool.py`) calculating priority score. | Score Formula: $0.6 \times \text{delay} + 0.4 \times \text{recency}$ |
| **Agent Orchestration**| LangGraph State Machine | 4-node state graph with dynamic intent routing (`agent/graph.py`). | 100% accurate edge routing by query intent |
| **Memory Persistence**| Thread Checkpointing | SQLite state checkpointer (`agent/checkpoint.py`) maintaining session multi-turn context. | Isolated thread state retention verified |
| **Input Guardrails** | PII Masking & Injection | Regex redaction (`[REDACTED_PHONE]`) & injection detection (`agent/guardrails.py`). | Fired and blocked in execution runs |
| **Output Guardrails**| Fallback Refusal | Low-confidence context checks redirecting to safe fallback messaging. | Refusal triggered on groundedness < **0.35** |
| **REST API** | FastAPI Service | Production endpoints (`/chat`, `/order/{id}`, `/health`) with CORS support. | Structured `ChatResponse` output verified |
| **Observability** | Structured Logging | Async request logger (`logs/requests.jsonl`) recording latency and trace IDs. | Schema tracking `trace_id` and `duration_sec` |
| **User Interface** | Streamlit Client App | Interactive chat UI (`ui.py`) with live routing indicators and admin document uploading. | Dynamic rendering & endpoint integration |

---

## 📌 Task 16: Project Completion & Final System Verification

The **Nykaa E-Commerce & Retail Support AI Agent** capstone implementation is complete. 

* **Full Pipeline Integration:** Streamlit UI (`ui.py`) $\rightarrow$ FastAPI Backend (`api/app.py`) $\rightarrow$ LangGraph State Machine (`agent/graph.py`) $\rightarrow$ FastMCP Tools / ChromaDB RAG.
* **Security & Observability:** Input PII masking, prompt-injection defense, output groundedness refusals, and structured `logs/requests.jsonl` trace tracking are active across all chat requests.

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
├── logs/                   # System log tracking
│   └── requests.jsonl      # Structured observability logs
├── rag/                    # Embeddings and document retriever modules
├── tools/                  # Tool abstractions and external handlers
│   └── order_tool.py       # Order tracking implementation
├── ui.py                   # Streamlit client web app
├── requirements.txt        # Dependencies
└── README.md

---

## Getting Started

### 1. Environment Setup

Initialize and activate a Python virtual environment:

python -m venv .venv

Activate environment:

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

---

### 2. Running Services

Run both backend and frontend processes simultaneously in separate terminal windows.

#### Terminal 1: FastAPI Backend
uvicorn api.app:app --reload --port 8000

* **API Documentation:** http://127.0.0.1:8000/docs
* **Health Check:** http://127.0.0.1:8000/health

#### Terminal 2: Streamlit Dashboard
streamlit run ui.py

* **Web Dashboard:** http://127.0.0.1:8501

---

## System Verification

Run tests to verify individual subsystem functionality:

* **Guardrails:**
  python -m agent.guardrails

* **Checkpoints:**
  python -m agent.checkpoint

* **Human Interruption & Escalation:**
  python -m agent.escalation

* **RAG Triad Metrics:**
  python -m rag.evaluate_triad