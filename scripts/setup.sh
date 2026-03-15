#!/bin/bash

# Stock Insight App - Setup Script
# This script installs all dependencies for frontend and backend

set -e  # Exit on error

echo "🚀 Setting up Stock Insight App..."
echo ""

# Frontend Setup
echo "📦 Installing Frontend dependencies..."
cd frontend
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found in frontend directory"
    exit 1
fi
npm install
echo "✅ Frontend dependencies installed"
echo ""

# Backend Setup
echo "🐍 Installing Backend dependencies..."
cd ../backend
if [ ! -f "requirements-dev.txt" ]; then
    echo "❌ Error: requirements-dev.txt not found in backend directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
echo "✅ Backend dependencies installed"
echo ""

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up environment variables:"
echo "   - Frontend: Copy frontend/.env.example to frontend/.env.local"
echo "   - Backend: Copy backend/.env.example to backend/.env"
echo ""
echo "2. Start development servers:"
echo "   - Frontend: cd frontend && npm run dev"
echo "   - Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
