#!/bin/bash
set -e

echo "=== Starting Nykaa Support AI Agent Services ==="

# 1. Ensure index/data directory exists (Skip heavy re-indexing on boot)
if [ ! -d "chroma_db" ] && [ -f "rag/index.py" ]; then
    echo "No existing vector index found. Running indexer once..."
    python dataset.py || true
    python -m rag.index || true
fi

# 2. Launch FastAPI backend in the background on port 8000
echo "Starting FastAPI backend on port 8000..."
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# 3. Wait for FastAPI to initialize models & DB connection
echo "Waiting 5 seconds for backend initialization..."
sleep 5

# 4. Launch Streamlit frontend on Render's assigned PORT
PORT="${PORT:-8501}"
echo "Starting Streamlit frontend on port $PORT..."
exec streamlit run UI.py --server.port "$PORT" --server.address 0.0.0.0