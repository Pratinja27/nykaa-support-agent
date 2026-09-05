#!/bin/bash

# Ensure order dataset and ChromaDB collection exist
python dataset.py
python -m rag.index

# Start FastAPI backend in the background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to spin up
sleep 5

# Use Render's PORT variable if available, default to 8501
PORT="${PORT:-8501}"

# Start Streamlit frontend
exec streamlit run UI.py --server.port $PORT --server.address 0.0.0.0