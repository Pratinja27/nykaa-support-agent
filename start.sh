#!/bin/bash

# 1. Run indexer only if needed (already built in Docker, but safe fallback)
python dataset.py
python -m rag.index

# 2. Launch FastAPI in background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# 3. Give FastAPI 10 seconds to load models and ChromaDB fully
sleep 10

# 4. Launch Streamlit
PORT="${PORT:-8501}"
exec streamlit run UI.py --server.port $PORT --server.address 0.0.0.0