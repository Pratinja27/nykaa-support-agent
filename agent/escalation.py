import os
from agent.checkpoint import get_sqlite_checkpointer
from agent.graph import build_graph


def run_hitl_demo():
    checkpointer = get_sqlite_checkpointer()
    
    # Interrupt execution before the response_node is reached
    graph_app = build_graph(
        checkpointer=checkpointer, 
        interrupt_before=["response_node"]
    )

    thread_id = "escalation_thread_999"
    config = {"configurable": {"thread_id": thread_id}}

    print("=== STEP 1: EXECUTION UNTIL INTERRUPT (BEFORE RESPONSE NODE) ===")
    input_data = {
        "thread_id": thread_id,
        "query": "What is the status of ORD1001?"
    }

    # Invoke graph - will interrupt before response_node
    graph_app.invoke(input_data, config=config)

    # Check state at interrupt point
    state_at_interrupt = graph_app.get_state(config)
    print("Next node pending execution:", state_at_interrupt.next)
    print("Order Result in State     :", state_at_interrupt.values.get("order_result"))

    print("\n=== STEP 2: HUMAN APPROVAL / RESUME EXECUTION ===")
    # Resuming execution from the checkpoint by passing None as input
    resumed_result = graph_app.invoke(None, config=config)
    print("Resumed Execution Output  :", resumed_result.get("final_response"))

    # Verify final state after resume
    final_state = graph_app.get_state(config)
    print("\n=== FINAL STATE CHECK ===")
    print("Next node to execute      :", final_state.next)


if __name__ == "__main__":
    run_hitl_demo()