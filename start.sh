#!/bin/bash

# Populate vector database
python dataset.py

# Start FastAPI backend in background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# Wait 5 seconds to give FastAPI time to spin up completely
sleep 5

# Use Render's PORT variable if available, default to 8501
PORT="${PORT:-8501}"

# Start Streamlit frontend
exec streamlit run UI.py --server.port $PORT --server.address 0.0.0.0