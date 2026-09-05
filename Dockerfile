FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . .

# Pre-build ChromaDB vector collection during the Docker build phase
RUN python dataset.py

# Expose Streamlit port
EXPOSE 8501

# Grant execution permission to the script
RUN chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]