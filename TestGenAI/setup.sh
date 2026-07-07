#!/bin/bash
# setup.sh - Complete setup script for TestGen AI

echo "🚀 Setting up TestGen AI..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads generated_tests

# Copy .env example if it doesn't exist
if [ ! -f .env ]; then
    echo "🔑 Creating .env file..."
    cp .env.example .env
    echo "Please edit .env and add your API keys"
fi

# Check for system dependencies
echo "🔍 Checking system dependencies..."

# Check Python
python --version

# Check Node.js (for JavaScript testing)
if command -v node &> /dev/null; then
    echo "✅ Node.js installed: $(node --version)"
else
    echo "⚠️  Node.js not found. Install for JavaScript testing:"
    echo "   https://nodejs.org/"
fi

# Check Java (for Java testing)
if command -v java &> /dev/null; then
    echo "✅ Java installed: $(java -version 2>&1 | head -n 1)"
    echo "   Download JUnit JAR and set JUNIT_JAR in .env"
else
    echo "⚠️  Java not found. Install for Java testing:"
    echo "   https://adoptium.net/"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  source .venv/bin/activate"
echo "  python app.py"
echo ""
echo "Open http://localhost:5000 in your browser"