import streamlit as st
import os
import json
import uuid
import time
import requests

from agent.guardrails import mask_pii, detect_injection

st.set_page_config(page_title="Nykaa Support Agent", page_icon="🛍️", layout="wide")

st.title("🛍️ Nykaa Support AI Agent")

# Backend API Configuration
# Updated to match your exact Render service URL
raw_url = os.getenv("BACKEND_URL", "https://nykaa-support-agent.onrender.com/")
BACKEND_URL = raw_url.strip().rstrip("/")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"thread_{uuid.uuid4().hex[:6]}"

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
    st.header("📄 Add KB Document")
    doc_filename = st.text_input("Filename", value="policies/returns.txt")
    doc_content = st.text_area("Content", value="Nykaa return policy allows returns within 15 days.")

    if st.button("Add Document"):
        kb_path = os.path.join("data", "knowledge_base", os.path.basename(doc_filename))
        os.makedirs(os.path.dirname(kb_path), exist_ok=True)
        with open(kb_path, "w", encoding="utf-8") as f:
            f.write(doc_content)
        st.success(f"Added `{doc_filename}` successfully!")

    st.markdown("---")
    st.header("📜 Live Log Stream")
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
        payload = {
            "thread_id": st.session_state.thread_id,
            "query": masked_query
        }

        try:
            response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
            duration = round(time.time() - start_time, 4)

            if response.status_code == 200:
                data = response.json()
                route = data.get("route", "unknown")
                final_res = data.get("final_response", "No response generated.")

                log_entry = {
                    "trace_id": trace_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "duration_sec": duration,
                    "thread_id": st.session_state.thread_id,
                    "query_masked": masked_query,
                    "route": route,
                    "final_response": final_res
                }
                log_request(log_entry)

                reply_content = f"{final_res}\n\n*`[Route: {route}]`*"
                st.session_state.messages.append({"role": "assistant", "content": reply_content})
                with st.chat_message("assistant"):
                    st.markdown(reply_content)
            else:
                st.error(f"Backend API Error ({response.status_code}) at target `{BACKEND_URL}/chat`: {response.text}")

        except Exception as e:
            st.error(f"Failed to connect to FastAPI backend at `{BACKEND_URL}`. Ensure server is running. Error: {str(e)}")