# Voice Bot - AI Operator Stess Test

A voice bot that calls an AI phone operator and stress-tests it with various scenarios (scheduling, cancellations, edge cases, etc.), then analyzes the conversation logs for bugs.

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Twilio account](https://console.twilio.com) with a phone number
- [Google AI Studio API Key](https://ai.google.dev/gemini-api/docs/api-key) (for Gemini)
- A public URL for webhooks (e.g., [ngrok](https://ngrok.com/))

## Quick Start (Docker - recommended)

1. **Clone the repo and set up environment variables:**
    ```bash
    cp .env.example .env
    # Edit .env with your actual credentials
    ```

2. **Start ngrok** (in a separate terminal):
    ```bash
    ngrok http 8080
    ```

3. **Copy the ngrok public URL** into your `.env` file as `WEBHOOK_URL`.


4. **Build Docker Image & Run:**
    ```bash
    sudo docker compose up --build -d
    ```

    ```bash
    sudo docker compose exec voice-bot bash -c "./run.sh"
    ```

## Environment Variables
| Variable | Description |
|---|---|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token |
| `TWILIO_NUMBER` | Your Twilio phone number (E.164 format) |
| `TEST_NUMBER` | The clinic number to call |
| `MY_NUMBER` | Your personal number (optional) |
| `GOOGLE_API_KEY` | Google AI Studio API key for Gemini |
| `WEBHOOK_URL` | Your public server URL (e.g., ngrok URL) |

## Analyzing Logs
After test calls complete, conversation logs are saved in `logs/`. To generate summaries:
```bash
sudo docker compose run voice-bot python3 src/analyzer.py
```

Analysis summaries are saved in `analysis/`.

## Changing Test Scenarios

The bot supports multiple test scenarios. To switch scenarios, change the index on **line 43** of `src/app.py`:

```python3
scenario = scenarios[8]  # Change the index to select a different scenario
```

Available scenarios (by index):
| Index | Scenario |
|-------|----------|
| 0 | `scheduling` |
| 1 | `refill` |
| 2 | `reschedule` |
| 3 | `cancel` |
| 4 | `complex_multi_request` |
| 5 | `urgent_edge_case` |
| 6 | `memory_stress_test` |
| 7 | `hallucination_detection` |
| 8 | `rapid_interruption_simulation` |
| 9 | `ambiguous_request` |
| 10 | `boundary_condition_test` |
| 11 | `information_overload` |

> **Note:** The `cancel` scenario runs in different language. All other scenarios run in English (`en-US`).

## Project Structure
```text
├── src/
│   ├── app.py                 # FastAPI webhook server
│   ├── bot.py                 # Twilio call initiator
│   ├── conversation.py        # LLM conversation handler (Gemini)
│   ├── conversation_logger.py # Logs conversations to text files
│   ├── analyzer.py            # Post-call log analysis
│   └── prompts/
│       └── prompt.json        # Scenario prompts
├── logs/                      # Conversation logs (auto-generated)
├── analysis/                  # Analysis summaries (auto-generated)
├── ARCHITECTURE.md            # Arch doc
├── CONSOLICATED_BUG_REPORT.md # Bug report
├── Dockerfile
├── docker-compose.yml          
├── requirements.txt           
├── README.md                  # Readme
├── run.sh                     # main shell script
└── .env.example               # Template for environment variables
```