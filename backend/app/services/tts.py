import asyncio
import httpx
import json
import io
import logging
from typing import Optional, Dict, Any, AsyncGenerator, Union
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class MurfTTSService:
    """
    Real-time Text-to-Speech service using Murf AI Falcon model
    Ultra-fast TTS with <130ms latency
    Supports multiple Indian languages and accents
    """
    
    # Murf AI voice mappings for different languages and genders
    VOICE_MAPPINGS = {
        # English voices
        "en-US": {
            "male": ["en-US-matthew", "en-US-alex", "en-US-daniel"],
            "female": ["en-US-sophia", "en-US-emma", "en-US-ava"]
        },
        "en-GB": {
            "male": ["en-GB-george", "en-GB-james"],
            "female": ["en-GB-lily", "en-GB-charlotte"]
        },
        "en-AU": {
            "male": ["en-AU-william"],
            "female": ["en-AU-olivia"]
        },
        "en-IN": {
            "male": ["en-IN-arjun", "en-IN-rohan"],
            "female": ["en-IN-aditi", "en-IN-priya"]
        },
        
        # Hindi voices
        "hi-IN": {
            "male": ["hi-IN-aarav", "hi-IN-vikram"],
            "female": ["hi-IN-ananya", "hi-IN-kavya"]
        },
        
        # Tamil voices
        "ta-IN": {
            "male": ["ta-IN-kamal", "ta-IN-surya"],
            "female": ["ta-IN-meera", "ta-IN-divya"]
        },
        
        # Telugu voices
        "te-IN": {
            "male": ["te-IN-ravi", "te-IN-krishna"],
            "female": ["te-IN-lakshmi", "te-IN-swathi"]
        },
        
        # Bengali voices
        "bn-IN": {
            "male": ["bn-IN-arjun"],
            "female": ["bn-IN-ishita"]
        },
        
        # Gujarati voices
        "gu-IN": {
            "male": ["gu-IN-dhruv"],
            "female": ["gu-IN-diya"]
        },
        
        # Kannada voices
        "kn-IN": {
            "male": ["kn-IN-gagan"],
            "female": ["kn-IN-sapna"]
        },
        
        # Malayalam voices
        "ml-IN": {
            "male": ["ml-IN-midhun"],
            "female": ["ml-IN-sobhana"]
        },
        
        # Marathi voices
        "mr-IN": {
            "male": ["mr-IN-aadarsh"],
            "female": ["mr-IN-aarohi"]
        }
    }
    
    def __init__(self):
        self.api_key = settings.MURF_API_KEY
        if not self.api_key:
            raise ValueError("MURF_API_KEY is required but not set")
        
        self.base_url = "https://global.api.murf.ai/v1/speech"
        self.stream_url = f"{self.base_url}/stream"
        self.generate_url = f"{self.base_url}/generate"
        
        # Default configuration for ultra-fast streaming
        self.default_config = {
            "model": "FALCON",  # Ultra-fast model <130ms
            "format": "MP3",
            "sampleRate": 24000,
            "channelType": "MONO",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0
        }
    
    def get_voice_id(
        self, 
        language: str = "en-IN", 
        gender: str = "female", 
        voice_index: int = 0
    ) -> str:
        """
        Get appropriate voice ID based on language and gender preference
        """
        if language not in self.VOICE_MAPPINGS:
            logger.warning(f"Language {language} not supported, falling back to en-IN")
            language = "en-IN"
            
        if gender not in self.VOICE_MAPPINGS[language]:
            gender = "female"  # Default to female
            
        voices = self.VOICE_MAPPINGS[language][gender]
        
        if voice_index >= len(voices):
            voice_index = 0
            
        return voices[voice_index]
    
    async def stream_speech(
        self,
        text: str,
        language: str = "en-IN",
        gender: str = "female",
        voice_index: int = 0,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream speech synthesis in real-time
        Ultra-fast streaming with <130ms latency
        """
        voice_id = self.get_voice_id(language, gender, voice_index)
        
        # Merge custom config with defaults
        config = {**self.default_config, **kwargs}
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "voice_id": voice_id,
            "text": text,
            "multi_native_locale": language,
            **config
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST", 
                    self.stream_url, 
                    headers=headers, 
                    json=data
                ) as response:
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Murf API error: {response.status_code} - {error_text}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"TTS streaming failed: {error_text}"
                        )
                    
                    # Stream audio chunks in real-time
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        if chunk:
                            yield chunk
                            
        except httpx.TimeoutException:
            logger.error("TTS streaming timeout")
            raise HTTPException(status_code=408, detail="TTS streaming timeout")
        except Exception as e:
            logger.error(f"TTS streaming error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"TTS streaming failed: {str(e)}")
    
    async def generate_speech(
        self,
        text: str,
        language: str = "en-IN",
        gender: str = "female",
        voice_index: int = 0,
        output_format: str = "MP3",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate speech synthesis (non-streaming)
        Returns audio data and metadata
        """
        voice_id = self.get_voice_id(language, gender, voice_index)
        
        config = {**self.default_config, **kwargs}
        config["format"] = output_format.upper()
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "voice_id": voice_id,
            "text": text,
            "multi_native_locale": language,
            **config
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.generate_url,
                    headers=headers,
                    json=data
                )
                
            if response.status_code == 200:
                # Assuming the response contains audio data
                return {
                    "success": True,
                    "audio_data": response.content,
                    "format": output_format,
                    "language": language,
                    "voice_id": voice_id,
                    "sample_rate": config["sampleRate"],
                    "duration_ms": len(response.content) * 1000 // (config["sampleRate"] * 2),  # Approximate
                }
            else:
                logger.error(f"Murf API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "audio_data": None
                }
                
        except Exception as e:
            logger.error(f"TTS generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": None
            }
    
    async def stream_speech_chunks(
        self,
        text_chunks: AsyncGenerator[str, None],
        language: str = "en-IN",
        gender: str = "female",
        voice_index: int = 0,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream speech for incoming text chunks (for real-time conversation)
        Perfect for streaming AI responses as they're generated
        """
        async for text_chunk in text_chunks:
            if text_chunk.strip():  # Skip empty chunks
                async for audio_chunk in self.stream_speech(
                    text_chunk, language, gender, voice_index, **kwargs
                ):
                    yield audio_chunk
    
    def get_supported_languages(self) -> Dict[str, Dict[str, list]]:
        """
        Get all supported languages and voices
        """
        return self.VOICE_MAPPINGS.copy()
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """
        Get information about a specific language
        """
        if language in self.VOICE_MAPPINGS:
            return {
                "language": language,
                "supported": True,
                "voices": self.VOICE_MAPPINGS[language]
            }
        else:
            return {
                "language": language,
                "supported": False,
                "voices": {}
            }


class RealTimeTTSManager:
    """
    Manager for real-time TTS operations
    Handles multiple concurrent TTS requests
    """
    
    def __init__(self):
        self.tts_service = MurfTTSService()
        self.active_streams = {}
    
    async def create_stream_session(
        self, 
        session_id: str,
        language: str = "en-IN",
        gender: str = "female",
        voice_index: int = 0
    ):
        """
        Create a new TTS streaming session
        """
        self.active_streams[session_id] = {
            "language": language,
            "gender": gender,
            "voice_index": voice_index,
            "created_at": asyncio.get_event_loop().time()
        }
    
    async def stream_for_session(
        self,
        session_id: str,
        text: str
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS for a specific session
        """
        if session_id not in self.active_streams:
            raise ValueError(f"Session {session_id} not found")
        
        session_config = self.active_streams[session_id]
        
        async for chunk in self.tts_service.stream_speech(
            text=text,
            language=session_config["language"],
            gender=session_config["gender"],
            voice_index=session_config["voice_index"]
        ):
            yield chunk
    
    async def close_session(self, session_id: str):
        """
        Close a TTS session
        """
        if session_id in self.active_streams:
            del self.active_streams[session_id]


# Global TTS service instances
tts_service = MurfTTSService()
realtime_tts_manager = RealTimeTTSManager()


# Helper functions for easy integration
async def text_to_speech(
    text: str,
    language: str = "en-IN",
    gender: str = "female",
    voice_index: int = 0,
    output_format: str = "MP3"
) -> Dict[str, Any]:
    """
    Quick TTS function for integration
    """
    return await tts_service.generate_speech(
        text, language, gender, voice_index, output_format
    )


async def stream_text_to_speech(
    text: str,
    language: str = "en-IN",
    gender: str = "female",
    voice_index: int = 0
) -> AsyncGenerator[bytes, None]:
    """
    Stream TTS function for integration
    """
    async for chunk in tts_service.stream_speech(text, language, gender, voice_index):
        yield chunk


def get_available_voices() -> Dict[str, Dict[str, list]]:
    """
    Get all available voices
    """
    return tts_service.get_supported_languages()


async def create_realtime_session(
    session_id: str,
    language: str = "en-IN",
    gender: str = "female",
    voice_index: int = 0
):
    """
    Create real-time TTS session for conversations
    """
    await realtime_tts_manager.create_stream_session(
        session_id, language, gender, voice_index
    )


async def stream_for_conversation(
    session_id: str,
    text: str
) -> AsyncGenerator[bytes, None]:
    """
    Stream TTS for ongoing conversation
    """
    async for chunk in realtime_tts_manager.stream_for_session(session_id, text):
        yield chunk