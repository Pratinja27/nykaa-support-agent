import streamlit as st
import os
import json
import uuid
import time

from agent.graph import build_graph
from agent.guardrails import mask_pii, detect_injection
from agent.schema import AgentResponseSchema

st.set_page_config(page_title="Nykaa Support Agent", page_icon="🛍️", layout="wide")

st.title("🛍️ Nykaa Support AI Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"thread_{uuid.uuid4().hex[:6]}"

@st.cache_resource
def get_agent_graph():
    return build_graph()

graph_app = get_agent_graph()

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "requests.jsonl")
os.makedirs(LOG_DIR, exist_ok=True)

def log_request(log_data: dict):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data) + "\n")

with st.sidebar:
    st.header("⚙️ Session Info")
    st.text_input("Thread ID", value=st.session_state.thread_id, disabled=True)

    st.markdown("---")
    st.header("📄 Add KB Document (Task 11)")
    doc_filename = st.text_input("Filename", value="policies/returns.txt")
    doc_content = st.text_area("Content", value="Nykaa return policy allows returns within 15 days.")

    if st.button("Add Document"):
        kb_path = os.path.join("data", "knowledge_base", os.path.basename(doc_filename))
        os.makedirs(os.path.dirname(kb_path), exist_ok=True)
        with open(kb_path, "w", encoding="utf-8") as f:
            f.write(doc_content)
        st.success(f"Added `{doc_filename}` successfully!")

    st.markdown("---")
    st.header("📜 Live Log Stream (Task 12)")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
            if logs:
                st.json(json.loads(logs[-1]))

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question (e.g. 'Status of ORD1001' or phone '9876543210')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    start_time = time.time()
    trace_id = str(uuid.uuid4())

    if detect_injection(prompt):
        err_msg = "🚨 **Security Policy Violation**: Prompt injection attempt detected."
        st.session_state.messages.append({"role": "assistant", "content": err_msg})
        with st.chat_message("assistant"):
            st.error(err_msg)
    else:
        masked_query = mask_pii(prompt)
        graph_input = {"thread_id": st.session_state.thread_id, "query": masked_query}
        result = graph_app.invoke(graph_input)
        duration = round(time.time() - start_time, 4)

        validated_response = AgentResponseSchema(
            thread_id=st.session_state.thread_id,
            query=masked_query,
            route=result.get("route", "rag"),
            final_response=result.get("final_response", "No response generated."),
            source=result.get("source", "system"),
            metadata={"trace_id": trace_id}
        )

        log_entry = {
            "trace_id": trace_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_sec": duration,
            "thread_id": st.session_state.thread_id,
            "query_masked": masked_query,
            "route": validated_response.route,
            "final_response": validated_response.final_response
        }
        log_request(log_entry)

        reply_content = f"{validated_response.final_response}\n\n*`[Route: {validated_response.route} | Source: {validated_response.source}]`*"
        st.session_state.messages.append({"role": "assistant", "content": reply_content})
        with st.chat_message("assistant"):
            st.markdown(reply_content)