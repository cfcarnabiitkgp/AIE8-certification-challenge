#!/bin/bash

# Run script for the backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Qdrant if not running (optional)
# docker run -p 6333:6333 qdrant/qdrant

# Run the FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

