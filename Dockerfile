# Dockerfile for the voice bot

FROM python:3.12-slim
WORKDIR /app

# Install project dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose the port
EXPOSE 8080

# Default command: start the FastAPI server and the bot
CMD ["sh", "-c", "cd src && uvicorn app:app --host 0.0.0.0 --port 8080 & sleep 3 && python3 bot.py && wait"]