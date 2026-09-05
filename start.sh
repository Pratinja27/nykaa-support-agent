#!/bin/bash

# Start FastAPI server in the background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# Use Render's PORT variable if available, otherwise default to 8501
PORT="${PORT:-8501}"

# Start Streamlit app in the foreground
exec streamlit run ui.py --server.port $PORT --server.address 0.0.0.0