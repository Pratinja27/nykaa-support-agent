import streamlit as st
import os
import sys
import json
import uuid
import time
import requests
import subprocess

from agent.guardrails import mask_pii, detect_injection

PAGE_ICON = "logo.png" if os.path.exists("logo.png") else "🛍️"
st.set_page_config(page_title="Nykaa Support Agent", page_icon=PAGE_ICON, layout="wide")

# Header
col1, col2 = st.columns([0.08, 0.92], vertical_alignment="center")
with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=60)
    else:
        st.write("🛍️")
with col2:
    st.title("Nykaa Support AI Agent")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

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


GREETINGS = ["hi", "hello", "hey", "good morning", "good evening", "hi there"]
THANK_YOU_PHRASES = [
    "thank you", "thanks", "thank u", "thanks a lot",
    "thats alright", "that's alright", "okay thank you", "ok thanks"
]

with st.sidebar:
    st.header("⚙️ Session Info")
    st.text_input("Thread ID", value=st.session_state.thread_id, disabled=True)

    st.markdown("---")
    st.header("📄 Add KB Document")

    # Guidance note for evaluators
    st.info("💡 **Format Tip:** Start line 1 with `Document ID: KBxxx` so RAG metadata tags correctly.")

    with st.expander("📋 View Document Template"):
        st.code(
            "Document ID: KB005\nTopic: Cancellation Policy\n\nCustomers can cancel orders in 'Placed' status immediately.",
            language="text"
        )

    doc_filename = st.text_input("Filename", value="cancellation_policy.txt")
    doc_content = st.text_area(
        "Content",
        value="Document ID: KB005\nTopic: Order Cancellation\n\nCustomers can cancel any order free of charge as long as the status is 'Placed' or 'Processing'. Once an order status changes to 'Shipped', direct cancellation is no longer available.",
        height=150
    )

    if st.button("Add Document"):
        kb_path = os.path.join("data", "knowledge_base", os.path.basename(doc_filename))
        os.makedirs(os.path.dirname(kb_path), exist_ok=True)

        # 1. Save file to disk
        with open(kb_path, "w", encoding="utf-8") as f:
            f.write(doc_content)

        # 2. Trigger runtime vector re-indexing for ChromaDB using current environment
        try:
            with st.spinner("Re-indexing vector database..."):
                result = subprocess.run(
                    [sys.executable, "-m", "rag.index"],
                    capture_output=True,
                    text=True,
                    check=True
                )
            st.success(f"Added and indexed `{os.path.basename(doc_filename)}` successfully!")
        except subprocess.CalledProcessError as e:
            st.error(f"Saved file, but vector re-indexing failed:\n\n```\n{e.stderr}\n```")

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

    clean_prompt = prompt.strip().lower()

    if any(phrase == clean_prompt or clean_prompt.startswith(phrase) for phrase in THANK_YOU_PHRASES):
        reply = "You're very welcome! 😊 Let me know if you need help with anything else on Nykaa!"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    elif clean_prompt in GREETINGS:
        reply = "Hello! 👋 Welcome to Nykaa Support. How can I assist you with your orders or products today?"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

    elif detect_injection(prompt):
        err_msg = "🚨 **Security Policy Violation**: Prompt injection attempt detected."
        st.session_state.messages.append({"role": "assistant", "content": err_msg})
        with st.chat_message("assistant"):
            st.error(err_msg)

    else:
        start_time = time.time()
        trace_id = str(uuid.uuid4())
        masked_query = mask_pii(prompt)
        payload = {
            "thread_id": st.session_state.thread_id,
            "query": masked_query
        }

        try:
            response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=30)
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
                st.error(f"Backend API Error ({response.status_code}) at target `{BACKEND_URL}/ask`: {response.text}")

        except Exception as e:
            st.error(f"Failed to connect to FastAPI backend at `{BACKEND_URL}`. Ensure server is running. Error: {str(e)}")