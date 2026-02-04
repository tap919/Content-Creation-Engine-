#!/bin/bash
# Development server script for Agentic Content Factory

set -e

# Default values
MODE="api"
HOST="0.0.0.0"
PORT="8000"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 Starting Agentic Content Factory..."
echo "   Mode: $MODE"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create output directories
mkdir -p output/images output/audio output/videos

# Run the application
python -m src.main --mode "$MODE" --host "$HOST" --port "$PORT"
