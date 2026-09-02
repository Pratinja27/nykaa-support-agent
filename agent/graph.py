import re
from typing import TypedDict, Optional, List, Dict

from langgraph.graph import StateGraph, END

from tools.order_tool import check_order_status
from rag.generator import generate_answer
from memory.conversation_memory import load_memory, add_message


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------

class GraphState(TypedDict, total=False):
    thread_id: str
    query: str
    history: List[Dict[str, str]]
    route: str
    rag_result: Optional[dict]
    order_result: Optional[dict]
    final_response: str


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

ORDER_ID_PATTERN = re.compile(r"\bORD\d+\b", re.IGNORECASE)

ORDER_INTENT_PATTERNS = [
    r"\border\s+status\b",
    r"\bstatus\s+of\s+(my\s+)?order\b",
    r"\btrack\s+(my\s+)?order\b",
    r"\bwhere\s+is\s+my\s+order\b",
    r"\bwhere('?s| is)\s+my\s+order\b",
    r"\bcheck\s+(my\s+)?order\b",
    r"\bstatus\s+of\s+ord\d+\b",
]


def _has_order_id(query: str) -> bool:
    return bool(ORDER_ID_PATTERN.search(query))


def _has_order_intent(query: str) -> bool:
    lowered = query.lower()
    return any(re.search(pattern, lowered) for pattern in ORDER_INTENT_PATTERNS)


def _extract_order_id(query: str) -> Optional[str]:
    match = ORDER_ID_PATTERN.search(query)
    return match.group(0).upper() if match else None


def _extract_order_id_from_history(history: List[Dict[str, str]]) -> Optional[str]:
    """Look back through prior user turns for an order ID mentioned earlier."""
    for msg in history:
        if msg["role"] == "user":
            match = ORDER_ID_PATTERN.search(msg["content"])
            if match:
                return match.group(0).upper()
    return None


# ---------------------------------------------------------------------------
# NODES
# ---------------------------------------------------------------------------

def input_node(state: GraphState) -> GraphState:
    query = state["query"].strip()
    history = load_memory(state["thread_id"])
    return {"query": query, "history": history}


def router_node(state: GraphState) -> GraphState:
    query = state["query"]

    # Explicit order ID → always order route
    if _has_order_id(query):
        return {"route": "order"}

    # Explicit order-related intent → order route
    if _has_order_intent(query):
        return {"route": "order"}

    # Context-dependent status question:
    # If the user says "What is the status?" and an order
    # was previously mentioned in this conversation, route to order.
    if re.search(r"\bstatus\b", query.lower()):
        history = state.get("history", [])
        previous_order_id = _extract_order_id_from_history(history)

        if previous_order_id:
            return {"route": "order"}

    # Everything else → RAG
    return {"route": "rag"}


def route_decision(state: GraphState) -> str:
    return state["route"]


def rag_node(state: GraphState) -> GraphState:
    query = state["query"]
    result = generate_answer(query)
    return {"rag_result": result}


def order_node(state: GraphState) -> GraphState:
    query = state["query"]
    history = state.get("history", [])

    order_id = _extract_order_id(query)

    if order_id is None:
        order_id = _extract_order_id_from_history(history)

    if order_id is None:
        result = {
            "error": "I don't have an order ID from this conversation. "
                     "Please share your order ID (e.g. ORD1001)."
        }
    else:
        try:
            result = check_order_status(order_id)
        except ValueError as e:
            result = {"error": str(e)}

    return {"order_result": result}


def response_node(state: GraphState) -> GraphState:
    route = state["route"]

    if route == "order":
        order_result = state.get("order_result", {})
        if "error" in order_result:
            final_response = order_result["error"]
        else:
            final_response = (
                f"Order {order_result['record_id']} is currently "
                f"{order_result['status']}. "
                f"Order value: ₹{order_result['order_value_inr']}. "
                f"Escalation score: {order_result['escalation_score']} "
                f"(escalation recommended: {order_result['escalation_recommended']})."
            )
    else:
        rag_result = state.get("rag_result", {})
        final_response = rag_result.get("answer", "No answer available.")

    return {"final_response": final_response}


def memory_save_node(state: GraphState) -> GraphState:
    thread_id = state["thread_id"]
    add_message(thread_id, role="user", content=state["query"])
    add_message(thread_id, role="assistant", content=state["final_response"])
    return {}


# ---------------------------------------------------------------------------
# GRAPH ASSEMBLY
# ---------------------------------------------------------------------------

def build_graph(checkpointer=None, interrupt_before=None):
    workflow = StateGraph(GraphState)

    workflow.add_node("input_node", input_node)
    workflow.add_node("router_node", router_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("order_node", order_node)
    workflow.add_node("response_node", response_node)
    workflow.add_node("memory_save_node", memory_save_node)

    workflow.set_entry_point("input_node")

    workflow.add_edge("input_node", "router_node")

    workflow.add_conditional_edges(
        "router_node",
        route_decision,
        {
            "rag": "rag_node",
            "order": "order_node",
        },
    )

    workflow.add_edge("rag_node", "response_node")
    workflow.add_edge("order_node", "response_node")
    workflow.add_edge("response_node", "memory_save_node")
    workflow.add_edge("memory_save_node", END)

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before or []
    )
# ---------------------------------------------------------------------------
# TASK 8 DEMONSTRATION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from memory.conversation_memory import clear_thread

    app = build_graph()

    print("TASK 8 - MEMORY-AWARE LANGGRAPH AGENT")
    print("=" * 60)

    clear_thread("thread_001")
    clear_thread("thread_002")

    print("\nThread 001")
    for query in [
        "My order is ORD1001",
        "What is the status?",
        "What is the return policy for footwear?",
    ]:
        result = app.invoke({"thread_id": "thread_001", "query": query})
        print(f"User: {query}")
        print(f"Agent: {result['final_response']}\n")

    print("\nThread 002")
    result = app.invoke({
        "thread_id": "thread_002",
        "query": "What order did I mention earlier?"
    })
    print("User: What order did I mention earlier?")
    print(f"Agent: {result['final_response']}")