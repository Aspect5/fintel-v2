#!/bin/bash

# FinTel v2 Environment Setup Script

echo "🚀 Setting up FinTel v2 environment..."

# Create .env file from example if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📋 Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY (required for LLM functionality)"
    echo "   - ALPHA_VANTAGE_API_KEY (optional - will use mock data if not provided)"
    echo "   - FRED_API_KEY (optional - will use mock data if not provided)"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Check if Python virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Python environment set up"
else
    echo "✅ Python virtual environment already exists"
fi

# Check if npm packages are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
    echo "✅ npm dependencies installed"
else
    echo "✅ npm dependencies already installed"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "  npm run dev"
echo ""
echo "Note: The application will work with mock data even without API keys."
echo "Financial tools will use realistic mock data when API keys are not configured."