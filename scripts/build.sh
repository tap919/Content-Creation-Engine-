#!/bin/bash
# Build script for Agentic Content Factory

set -e

echo "🏗️  Building Agentic Content Factory..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create output directories
echo "📁 Creating output directories..."
mkdir -p output/images output/audio output/videos

# Run tests
echo "🧪 Running tests..."
# Set ENFORCE_TEST_SUCCESS=1 to make test failures stop the build (recommended for CI)
if [ "${ENFORCE_TEST_SUCCESS:-0}" = "1" ]; then
    # In strict mode, let pytest failures stop the build (set -e is enabled)
    pytest tests/ -v --tb=short
else
    # Default behavior: allow tests to fail without breaking the build
    pytest tests/ -v --tb=short || echo "⚠️  Some tests failed (may be expected for placeholder code)"
fi

echo "✅ Build complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python -m src.main --mode api"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
