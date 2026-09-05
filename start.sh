#!/bin/bash

# Run dataset script to build ChromaDB collection
python dataset.py

# Start FastAPI server in the background
uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# Use Render's PORT variable if available, default to 8501
PORT="${PORT:-8501}"

# Start Streamlit app
exec streamlit run UI.py --server.port $PORT --server.address 0.0.0.0