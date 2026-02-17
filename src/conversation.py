"""
    Conversation Handler:
    Processes transcripts from Twilio and generates LLM responses.
"""
import os
import re
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


env_path = Path(__file__).parent / '.env'
load_dotenv()

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

class ConversationHandler:
    """
        Handles conversation flow: Transcript -> LLM -> Response Text
    """
    def __init__(self, scenario: str= 'scheduling'):
        self.model = 'gemini-2.5-flash-lite'
        self.llm = ChatGoogleGenerativeAI(
            model = self.model,
            temperature = 0.5,
            streaming = True,
            api_key = os.getenv('GOOGLE_API_KEY'),
        )
        self.prompts = self._load_prompts()
        self.conversation_history: List = []
        self.scenario = scenario
        self.set_scenario(scenario)

    def _load_prompts(self) -> dict:
        prompt_path = Path(__file__).parent / 'prompts' / 'prompt_copy.json'
        with open(prompt_path, 'r') as f:
            prompts = json.load(f)
        return prompts
        
    def set_scenario(self, scenario: str):
        logger.info(f'Scenario changed to: {scenario}')
        self._add_system_message()

    def _add_system_message(self):
        # Add system message based on current scenario
        overview_text = self.prompts['overview']
        prompt_text = self.prompts['scenarios'][self.scenario]
        system_message = SystemMessage(content = f"{overview_text}\n\n{prompt_text}")
        self.conversation_history = [system_message]

    async def process_transcript(
        self, 
        transcript: str,
        stream: bool = False
        ) -> Optional[str]:
        """
            Process incoming transcript and get LLM response.
            Args:
                transcript: The transcribed text from Twilio
                media_stream_handler: Handler to send text chunks (required if stream=True)
                stream: True, if stream chunks as they arrive. False, if return full response at once.
            
            Returns:
                Tuple of 
                Response text to send back (or None if no response needed)
        """

        try:
            # Add agent message to history
            human_msg = HumanMessage(content = transcript)
            self.conversation_history.append(human_msg)

            if stream:
                # Skip for now, since we are using ConversationRelay to handle streaming.
                return None # Already sent via streaming
            else:
                return await self._get_full_response()
        
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            return None
        

    async def _get_full_response(self) -> str:
        """
            Get full response from LLM. (non-streaming)
        """
        try:
            response = await self.llm.ainvoke(self.conversation_history)
            assistant_msg = response.content

            # Add to history
            ai_msg = AIMessage(content = assistant_msg)
            self.conversation_history.append(ai_msg)

            return assistant_msg

        except Exception as e:
            logger.error(f"Error getting full response from LLM: {e}")
            return None
    
    # async def _stream_response(self, media_stream_handler) -> None:
    #     """
    #         Stream LLM response in chunk of sentences.
    #         Send complete sentences directly to Twilio as they're generated'.
    #         Returns None because chunks are sent via callback.
    #     """
    #     try:
    #         buffer = ""     # Buffer for partial/incomplete sentences
    #         full_response = ""

    #         async for chunk in self.llm.astream(self.conversation_history):
    #             if not chunk.content:
    #                 continue
                
    #             # Add chunk to buffer
    #             buffer += chunk.content
    #             full_response = chunk.content

    #             # Check for sentence boundaries
    #             sentences = self._extract_complete_sentences(buffer)

    #             # send complete sentences to Twilio
    #             for sentence in sentences['complete']:
    #                 await media_stream_handler.send_text(sentence)
                
    #             # Keep incomplete sentence in buffer
    #             buffer = sentences['incomplete']

    #         # Send any remaining text in buffer (if stream ended mid-sentence)
    #         if buffer.strip():
    #             await media_stream_handler.send_text(buffer)

    #         # Add complete response to history
    #         ai_msg = AIMessage(content = full_response.strip())
    #         self.conversation_history.append(ai_msg)

        
    #     except Exception as e:
    #         logger.error(f"Error streaming response: {e}")

    #         # If streaming fails, try to send what we have so far
    #         if buffer.strip():
    #             await media_stream_handler.send_text(buffer)
    #         return None


    # def _extract_complete_sentences(self, text: str) -> dict:
    #     """
    #         Extract complete sentences from text buffer.
    #         Args:
    #             text: Text buffer that may contain complete and incomplete sentences.
            
    #         Returns:
    #             dict with 'complete' (list of sentences) and 'incomplete' (remaining text)
    #     """
    #     # Pattern to match sentence endings: . ! ? followed by space or end of string.
    #     # Also need to handle cases like "Dr." or "Mrs." or "Mr." etc. that shouldn't break sentences.
    #     sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])(?=\s*$)'

    #     parts = re.split(sentence_endings, text)
    #     complete_sentences = []
    #     incomplete = ""

    #     for i, part in enumerate(parts):
    #         part = part.strip()
    #         if not part:
    #             continue

    #         if re.search(r'[.!?]$', part):
    #             complete_sentences.append(part)
    #         else:
    #             incomplete = part       # Likely a partial sentence
    #             if i < len(parts) - 1:
    #                 incomplete = ' '.join(parts[i:]).strip()
    #                 break
        
    #     # If no sentence endings found, everything is incomplete
    #     if not complete_sentences and text.strip():
    #         incomplete = text.strip()
        
    #     return {
    #         'complete': complete_sentences,
    #         'incomplete': incomplete
    #     }