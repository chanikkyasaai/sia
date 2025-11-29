import asyncio
import websockets
import json
import base64
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class SonioxSTTService:
    """
    Real-time Speech-to-Text service using Soniox API
    Supports multiple Indian languages: Hindi, Tamil, Telugu, English
    """
    
    SUPPORTED_LANGUAGES = {
        "en": "en",          # English
        "hi": "hi",          # Hindi
        "ta": "ta",          # Tamil
        "te": "te",          # Telugu
        "bn": "bn",          # Bengali
        "gu": "gu",          # Gujarati
        "kn": "kn",          # Kannada
        "ml": "ml",          # Malayalam
        "mr": "mr",          # Marathi
        "pa": "pa",          # Punjabi
    }
    
    def __init__(self):
        self.api_key = settings.SONIOX_API_KEY
        if not self.api_key:
            raise ValueError("SONIOX_API_KEY is required but not set")
        self.websocket_url = "wss://api.soniox.com/transcribe-websocket"

    async def start_realtime_transcription(
        self,
        language: str = "en",
        sample_rate: int = 16000
    ) -> 'RealtimeTranscriber':
        """
        Start a real-time transcription session
        """
        return RealtimeTranscriber(
            websocket_url=self.websocket_url,
            api_key=self.api_key,
            language=language,
            sample_rate=sample_rate
        )

    async def transcribe_audio_file(
        self, 
        audio_data: bytes, 
        language: str = "en",
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file (non-streaming)
        """
        try:
            import httpx
            
            url = "https://api.soniox.com/transcribe"
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Encode audio data to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            config = self._get_soniox_config(language)
            config.pop('api_key')  # Remove from config, it's in headers
            
            payload = {
                "audio": audio_base64,
                "audio_format": audio_format.upper(),
                **config
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=headers, 
                    json=payload, 
                    timeout=30.0
                )
                
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "transcript": result.get("transcript", ""),
                    "language": language,
                    "confidence": result.get("confidence", 0.0),
                    "words": result.get("words", [])
                }
            else:
                logger.error(f"Soniox API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "transcript": ""
                }
                
        except Exception as e:
            logger.error(f"STT transcription error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transcript": ""
            }


class RealtimeTranscriber:
    """
    Real-time transcriber using WebSocket connection to Soniox
    """

    def __init__(self, websocket_url: str, api_key: str, language: str, sample_rate: int):
        self.websocket_url = websocket_url
        self.api_key = api_key
        self.language = language
        self.sample_rate = sample_rate
        self.websocket = None
        self.is_connected = False

    async def connect(self):
        """
        Establish WebSocket connection
        """
        try:
            self.websocket = await websockets.connect(self.websocket_url)

            # Send configuration - Soniox uses minimal init
            init_message = {
                "api_key": self.api_key,
                "model": f"{self.language}_v1",  # e.g., "en_v1", "hi_v1"
            }
            await self.websocket.send(json.dumps(init_message))

            # Soniox doesn't send acknowledgment - it just waits for audio
            # Connection is ready immediately after sending init
            self.is_connected = True
            logger.info(f"Connected to Soniox WebSocket with model: {self.language}_v1")

        except Exception as e:
            logger.error(f"Failed to connect to Soniox: {str(e)}")
            raise

    async def send_audio(self, audio_chunk: bytes):
        """
        Send audio chunk for transcription
        """
        if not self.is_connected or not self.websocket:
            raise Exception("Not connected to Soniox")
            
        try:
            # Send binary audio data
            await self.websocket.send(audio_chunk)
        except Exception as e:
            logger.error(f"Error sending audio: {str(e)}")
            raise
    
    async def receive_transcription(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Receive and process transcription results
        """
        try:
            async for message in self.websocket:
                try:
                    result = json.loads(message)
                    final_words = result.get("final_words", [])
                    non_final_words = result.get("non_final_words", [])
                    
                    transcript = " ".join(w["text"] for w in final_words)
                    is_final = len(non_final_words) == 0
                    
                    if transcript or not is_final:
                        full_transcript = " ".join(w["text"] for w in (final_words + non_final_words))
                        yield {
                            "transcript": full_transcript,
                            "is_final": is_final,
                        }
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                    continue

        except Exception as e:
            logger.error(f"Error receiving transcription: {str(e)}")
            raise
    
    async def close(self):
        """
        Close WebSocket connection
        """
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from Soniox")


# Global STT service instance
stt_service = SonioxSTTService()


# Helper functions for easy integration
async def transcribe_audio(
    audio_data: bytes,
    language: str = "en",
    audio_format: str = "wav"
) -> Dict[str, Any]:
    """
    Quick transcription function for integration
    """
    return await stt_service.transcribe_audio_file(audio_data, language, audio_format)


async def start_live_transcription(
    language: str = "en",
    sample_rate: int = 16000
) -> RealtimeTranscriber:
    """
    Start live transcription session
    """
    transcriber = await stt_service.start_realtime_transcription(language, sample_rate)
    await transcriber.connect()
    return transcriber


def get_supported_languages() -> Dict[str, str]:
    """
    Get list of supported languages
    """
    return SonioxSTTService.SUPPORTED_LANGUAGES.copy()