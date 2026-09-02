import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from agent.graph import build_graph

# Ensure data directory exists
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "checkpoints.db")
os.makedirs(DB_DIR, exist_ok=True)


def get_sqlite_checkpointer():
    """Initializes and returns a persistent SqliteSaver checkpointer."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return SqliteSaver(conn)


def test_checkpointing():
    """Demonstrates state persistence and thread isolation across two threads."""
    checkpointer = get_sqlite_checkpointer()
    graph_app = build_graph(checkpointer=checkpointer)

    # Thread 1 Interaction
    config_thread_1 = {"configurable": {"thread_id": "user_session_101"}}
    input_1 = {"thread_id": "user_session_101", "query": "What is status of ORD1001?"}
    
    print("=== EXECUTING THREAD 1 (user_session_101) ===")
    res1 = graph_app.invoke(input_1, config=config_thread_1)
    print("Thread 1 Route:", res1.get("route"))
    print("Thread 1 Response:", res1.get("final_response"))

    # Thread 2 Interaction (Isolated Session)
    config_thread_2 = {"configurable": {"thread_id": "user_session_202"}}
    input_2 = {"thread_id": "user_session_202", "query": "My order is ORD1002, tell me status"}
    
    print("\n=== EXECUTING THREAD 2 (user_session_202) ===")
    res2 = graph_app.invoke(input_2, config=config_thread_2)
    print("Thread 2 Route:", res2.get("route"))
    print("Thread 2 Response:", res2.get("final_response"))

    # Verify Checkpoint Persistence in SQLite DB
    state_thread_1 = graph_app.get_state(config_thread_1)
    state_thread_2 = graph_app.get_state(config_thread_2)

    print("\n=============================================")
    print("=== CHECKPOINT STATE VERIFICATION ===")
    print("=============================================")
    print("DB Path Exists       :", os.path.exists(DB_PATH))
    print("Thread 1 Saved Query :", state_thread_1.values.get("query"))
    print("Thread 2 Saved Query :", state_thread_2.values.get("query"))


if __name__ == "__main__":
    test_checkpointing()