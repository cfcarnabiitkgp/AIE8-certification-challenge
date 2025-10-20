#!/bin/bash

# Quick start script for Research Paper Peer Review System
# This script helps you get started quickly

set -e

echo "=================================================="
echo "Research Paper Peer Review System - Quick Start"
echo "=================================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv is not installed!"
    echo "Installing uv package manager..."
    if command -v brew &> /dev/null; then
        brew install uv
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    echo "✓ uv installed successfully"
fi

# Check if Qdrant is running
echo "Checking if Qdrant is running..."
if ! curl -s http://localhost:6333 > /dev/null; then
    echo "⚠️  Qdrant is not running!"
    echo "Starting Qdrant with Docker..."
    docker run -d -p 6333:6333 -p 6334:6334 \
        -v $(pwd)/qdrant_storage:/qdrant/storage \
        --name qdrant \
        qdrant/qdrant
    echo "✓ Qdrant started"
    sleep 3
else
    echo "✓ Qdrant is already running"
fi

# Check for OpenAI API key
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "⚠️  Backend .env file not found!"
    echo "Creating .env from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your OPENAI_API_KEY"
    echo "The file is located at: backend/.env"
    echo ""
    read -p "Press Enter after adding your API key..."
fi

# Backend setup
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment with uv..."
    uv venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies from pyproject.toml..."
uv pip install -q -e .

echo "Starting backend server..."
echo "Backend will run at: http://localhost:8000"
.venv/bin/uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

if [ ! -f ".env.local" ] && [ -f ".env.local.example" ]; then
    cp .env.local.example .env.local
fi

echo "Starting frontend server..."
echo "Frontend will run at: http://localhost:3000"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================================="
echo "✓ Application started successfully!"
echo "=================================================="
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""
echo "To stop the application, press Ctrl+C"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait

