FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . .

# Generate dataset and build ChromaDB vector store
RUN python dataset.py && python -m rag.index

# Expose Streamlit port
EXPOSE 8501

# Grant execution permission to the script
RUN chmod +x start.sh

# Run startup script
CMD ["./start.sh"]