#!/bin/bash

clear
SCRIPT_DIR="$(pwd)"

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

source "$SCRIPT_DIR/voice_bot/bin/activate"

# === Start FastAPI server ===
echo "Starting FastAPI server..."
cd "$SCRIPT_DIR/src" && uvicorn app:app --host 0.0.0.0 --port 8080 --reload &
SERVER_PID=$!



sleep 3
echo ""
echo "Service started:"
echo "FastAPI server: http://localhost:8080" | lolcat
echo ""
echo "Press Ctrl+C to exit." | lolcat
echo ""


# === Run bot in background so script can continue ===
cd "$SCRIPT_DIR/src" && python3 bot.py &
BOT_PID=$!

wait