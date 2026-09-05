#!/bin/bash

# Run dataset script and wait for completion
echo "=== Building ChromaDB collection ==="
python dataset.py
echo "=== ChromaDB script finished ==="

# Start FastAPI backend in background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to initialize
sleep 5

# Use Render's PORT variable
PORT="${PORT:-8501}"

# Start Streamlit frontend
exec streamlit run UI.py --server.port $PORT --server.address 0.0.0.0