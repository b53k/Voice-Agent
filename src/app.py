'''
WEBHOOK HANDLER:
Handles incoming webhook callbacks from Twilio for call status updates.
Initiates Media Streams connection for full-duplex communication.
'''
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from twilio.twiml.voice_response import VoiceResponse, Connect
from conversation import ConversationHandler

env_path = Path(__file__).parent / '.env'
load_dotenv()

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

scenario = 'howdy'
if scenario == 'cancel':
    language = "hi-IN"
    tts_language = "hi-IN"
else:
    language = "en-US"
    tts_language = "en-US"

conversation_handler = ConversationHandler(scenario)

# ====================================================
# Create API Router
webhook_router = APIRouter(prefix = "/webhook", tags = ["webhook"])


@webhook_router.post("/answer")
async def answer_call(request: Request):
    """
        Handles incoming call from Twilio.
        Returns TwiML response to initiate Media Streams connection.
    """
    try:
        response = VoiceResponse()
        base_url = os.getenv("WEBHOOK_URL", '')

        # Convert to WebSocket URL
        wss_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://')

        connect = Connect() # ConversationRelay handles transcription & TTS automatically.
        connect.conversation_relay(url = f'{wss_url}/webhook/ws', language = language, tts_language = tts_language)
        
        response.append(connect)

        return Response(content = str(response), media_type = 'application/xml')
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))



# Websocket endpoint
@webhook_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
        Handle WebSocket connection from Twilio Media Streams.
        Bi-directional audio streaming between server and bot.
    """
    
    logger.info("WebSocket connection attempt received")

    # Log headers and query params for debugging
    #logger.info(f"WebSocket headers: {dict(websocket.headers)}")
    #logger.info(f"WebSocket query params: {dict(websocket.query_params)}")

    await websocket.accept()


    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Twilio sends "prompt" message when the user finishes a sentence.
            if message.get("type") == "prompt":
                operator_text = message.get("voicePrompt")
                logger.info(f" <<< Operator said: {operator_text}")

                #ai_reply = await conversation_handler.process_transcript(user_text)
                #ai_reply = "What's up Bipin? I will count from 1 to 10. 1 2 3 4 5 6 7 8 9 10."

                ai_reply = await conversation_handler.process_transcript(operator_text, stream = False)
                logger.info(f" >>> AI replied: {ai_reply}")

                # Send AI reply back to be spoken
                reply = {
                    "type": "text",
                    "token": ai_reply,
                    "last": True,   # Indicates the last token in the sequence.
                    "interruptible": True, # Indicates if the reply can be interrupted by user input.
                }

                await websocket.send_text(json.dumps(reply))

    except WebSocketDisconnect:
        logger.info(f"WebSocket Disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        raise HTTPException(status_code = 500, detail = str(e))


# ====================================================
# Create FASTAPI application
app = FastAPI(
    title = "Twilio Call Webhook Handler",
    description = "Handles incoming webhook callbacks from Twilio for call status updates.",
    version = "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], # Allow all origins for development purpose.
    allow_credentials = True,
    allow_methods = ["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers = ["*"], # Allows all headers (Authorization, Content-Type, etc.)
)

app.include_router(webhook_router)