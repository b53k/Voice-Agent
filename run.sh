#!/bin/bash

clear
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo ""
    echo "Stopping services..."
    # Kill all related processes
    pkill -f "uvicorn.*8080" 2>/dev/null

    sleep 2

    # Force kill if its still running
    pkill -9 -f "uvicorn.*8080" 2>/dev/null

    echo "Server Stopped."
    exit
}

trap cleanup INT TERM

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/voice_bot" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/voice_bot"
    source "$SCRIPT_DIR/voice_bot/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    source "$SCRIPT_DIR/voice_bot/bin/activate"
fi

# Check for .env file
if [ ! -f "$SCRIPT_DIR/src/.env" ] && [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "ERROR: No .env file found!"
    echo "Copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    exit 1
fi

# === Start FastAPI server ===
echo "Starting FastAPI server..."
cd "$SCRIPT_DIR/src" && uvicorn app:app --host 0.0.0.0 --port 8080 --reload &
SERVER_PID=$!


sleep 3
echo ""
echo "Service started:"
echo "FastAPI server: http://localhost:8080"
echo ""
echo "Press Ctrl+C to exit."
echo ""

# === Run bot in background so script can continue ===
cd "$SCRIPT_DIR/src" && python3 bot.py &
BOT_PID=$!

wait