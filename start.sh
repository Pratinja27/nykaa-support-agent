#!/bin/bash

# Start FastAPI server in the background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# Start Streamlit app in the foreground
exec streamlit run ui.py --server.port 8501 --server.address 0.0.0.0