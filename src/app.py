'''
WEBHOOK HANDLER:
Handles incoming webhook callbacks from Twilio for call status updates.
Initiates Media Streams connection for full-duplex communication.
'''
import os
import re
import json
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from twilio.twiml.voice_response import VoiceResponse, Connect
from conversation import ConversationHandler
from conversation_logger import ConversationLogger

env_path = Path(__file__).parent / '.env'
load_dotenv()

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

scenarios = [
    'scheduling',
    'refill',
    'reschedule',
    'cancel',
    'complex_multi_request',
    'urgent_edge_case',
    'memory_stress_test',
    'hallucination_detection',
    'rapid_interruption_simulation',
    'ambiguous_request',
    'boundary_condition_test',
    'information_overload'
]

scenario = scenarios[8]

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

    # Initialize conversation logger
    conversation_logger = ConversationLogger(scenario)

    # Message buffering to wait for complete operator messages.
    operator_message_buffer = []
    buffer_timeout_task = None
    SILENCE_TIMEOUT = 6.0  # seconds to wait for silence before flushing buffer.
    websocket_connected = True
    MAX_CHUNK_SIZE = 200 # Characters per chunk.
    
    async def process_buffered_messages():
        """
            Process buffered messages when we have a complete operator message.
        """
        nonlocal operator_message_buffer, buffer_timeout_task, websocket_connected

        if not operator_message_buffer or not websocket_connected:
            return # No messages to process or connection is closed.

        # Combine all buffered messages into one.
        full_operator_message = " ".join(operator_message_buffer)
        operator_message_buffer = []    # Clear buffer

        logger.info(f" >>> Operator Said: {full_operator_message}")

        conversation_logger.log_operator(full_operator_message)

        ai_reply = await conversation_handler.process_transcript(full_operator_message, stream = False)
        logger.info(f" >>> AI replied: {ai_reply}")

        if ai_reply and websocket_connected:
            # log patient message
            conversation_logger.log_patient(ai_reply)

            # Split long messages into smaller chunks to prevent TTS timeout.
            # Twilio Conversation Relay may work better with smaller chunks...idk!!!!

            if len(ai_reply) > MAX_CHUNK_SIZE:
                sentences = re.split(r'([.!?]+(?:\s+|$))', ai_reply)

                # Recombine sentences with punctuation.
                sentence_list = []
                for i in range(0, len(sentences), 2):
                    if i+1 < len(sentences):
                        sentence_list.append(sentences[i] + sentences[i+1])
                    elif sentences[i].strip():
                        sentence_list.append(sentences[i])
                
                # Group sentences into chunks
                chunks = []
                current_chunk = ""

                for sentence in sentence_list:
                    # If adding this sentence would exceed the chunk size, start new chunk.
                    if current_chunk and len(current_chunk) + len(sentence) > MAX_CHUNK_SIZE:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence
                
                # Add remaining chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            
            else:
                chunks = [ai_reply]

            # Send chunks incrementally to prevent TTS timeout.
            for i, chunk in enumerate(chunks):
                if not websocket_connected:
                    break

                is_last = (i == len(chunks) - 1)

                # Send AI reply back to be spoken
                reply = {
                    "type": "text",
                    "token": chunk,
                    "last": is_last,   # Indicates the last token in the sequence.
                    "interruptible": True, # Indicates if the reply can be interrupted by user input.
                }

                try:
                    await websocket.send_text(json.dumps(reply))

                    if not is_last:
                        await asyncio.sleep(0.5) # 500 ms delay between chunks.

                except WebSocketDisconnect:
                    websocket_connected = False
                    break


    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Twilio sends "prompt" message when the user finishes a sentence.
            if message.get("type") == "prompt":
                operator_text = message.get("voicePrompt")

                if operator_text and operator_text.strip():
                    # Add to buffer
                    operator_message_buffer.append(operator_text.strip())

                    # Cancel any existing timeout task.
                    if buffer_timeout_task and not buffer_timeout_task.done():
                        buffer_timeout_task.cancel()

                    # Start a new timeout - wait for SILENCE_TIMEOUT seconds of no new messages.
                    async def timeout_handler():
                        await asyncio.sleep(SILENCE_TIMEOUT)
                        await process_buffered_messages()

                    buffer_timeout_task = asyncio.create_task(timeout_handler())

                    

                # # log operator message
                # conversation_logger.log_operator(operator_text)

                # # Check if the message seems incomplete (doesn't end with punctuation)
                # is_incomplete = operator_text and not operator_text.rstrip().endswith(('.', '!', '?', ':', ';'))

                # # add small delay to ensure we're not responding too quickly.
                # if is_incomplete:
                #     await asyncio.sleep(6)  # wait 6 seconds before responding.
                # else:
                #     await asyncio.sleep(3)  # wait 3 seconds before responding.

                # ai_reply = await conversation_handler.process_transcript(operator_text, stream = False)
                # logger.info(f" >>> AI replied: {ai_reply}")

                # if ai_reply:
                #     # log patient message
                #     conversation_logger.log_patient(ai_reply)

                # # Send AI reply back to be spoken
                # reply = {
                #     "type": "text",
                #     "token": ai_reply,
                #     "last": True,   # Indicates the last token in the sequence.
                #     "interruptible": True, # Indicates if the reply can be interrupted by user input.
                # }

                # await websocket.send_text(json.dumps(reply))

    except WebSocketDisconnect:
        logger.info(f"WebSocket Disconnected")
        websocket_connected = False

        if buffer_timeout_task and not buffer_timeout_task.done():
            buffer_timeout_task.cancel()
            try:
                await buffer_timeout_task
            except asyncio.CancelledError:
                pass

        # Process any remaining buffered messages but don't try to send responses.
        if operator_message_buffer:
            full_operator_message = " ".join(operator_message_buffer)
            logger.info(f" >>> Operator Said: {full_operator_message}")
            conversation_logger.log_operator(full_operator_message)

        # Save the conversation log.
        conversation_logger.save()

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        conversation_logger.save()  # Save the conversation log even on error.
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