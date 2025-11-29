"""
Voice Conversation Manager with Intelligent Turn Detection and Barge-In Handling
Orchestrates STT → AI Agent → TTS pipeline with context preservation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime, timedelta
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class AudioBuffer:
    """Manages audio buffering and silence detection with VAD"""
    
    def __init__(
        self,
        silence_threshold: float = 0.02,  # Amplitude threshold for silence
        silence_duration: float = 1.5,     # Seconds of silence to trigger turn end
        sample_rate: int = 16000,
        chunk_duration: float = 0.1        # 100ms chunks
    ):
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self.buffer = bytearray()
        self.silence_chunks = 0
        self.silence_chunks_needed = int(silence_duration / chunk_duration)
        self.is_speaking = False
        self.speech_started = False
        
        # Rolling energy window for better VAD
        self.energy_window = deque(maxlen=5)
        
        logger.info(f"AudioBuffer initialized: threshold={silence_threshold}, "
                   f"silence_duration={silence_duration}s, chunk_size={self.chunk_size}")
    
    def add_audio(self, audio_data: bytes) -> None:
        """Add audio data to buffer"""
        self.buffer.extend(audio_data)
    
    def has_complete_chunk(self) -> bool:
        """Check if buffer has a complete chunk"""
        return len(self.buffer) >= self.chunk_size * 2  # 2 bytes per sample (16-bit)
    
    def get_chunk(self) -> Optional[bytes]:
        """Extract a chunk from buffer"""
        if not self.has_complete_chunk():
            return None
        
        chunk_bytes = self.chunk_size * 2
        chunk = bytes(self.buffer[:chunk_bytes])
        self.buffer = self.buffer[chunk_bytes:]
        return chunk
    
    def calculate_energy(self, audio_chunk: bytes) -> float:
        """Calculate RMS energy of audio chunk for VAD"""
        try:
            # Convert bytes to numpy array (16-bit PCM)
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            # Normalize to 0-1 range
            normalized_energy = rms / 32768.0
            return normalized_energy
        except Exception as e:
            logger.warning(f"Error calculating energy: {e}")
            return 0.0
    
    def detect_speech_activity(self, audio_chunk: bytes) -> Dict[str, Any]:
        """
        Detect voice activity and silence periods
        Returns dict with is_speaking, silence_detected, and should_end_turn flags
        """
        energy = self.calculate_energy(audio_chunk)
        self.energy_window.append(energy)
        
        # Use average energy over window for stability
        avg_energy = sum(self.energy_window) / len(self.energy_window) if self.energy_window else 0.0
        
        # Detect if currently speaking
        currently_speaking = avg_energy > self.silence_threshold
        
        # Track speech start
        if currently_speaking and not self.speech_started:
            self.speech_started = True
            self.is_speaking = True
            self.silence_chunks = 0
            logger.debug(f"Speech started - Energy: {avg_energy:.4f}")
        
        # Track silence periods
        if self.speech_started:
            if not currently_speaking:
                self.silence_chunks += 1
            else:
                self.silence_chunks = 0
                self.is_speaking = True
        
        # Determine if turn should end (sufficient silence after speech)
        should_end_turn = (
            self.speech_started and 
            self.silence_chunks >= self.silence_chunks_needed
        )
        
        return {
            "is_speaking": currently_speaking,
            "avg_energy": avg_energy,
            "silence_detected": not currently_speaking and self.speech_started,
            "silence_chunks": self.silence_chunks,
            "should_end_turn": should_end_turn,
            "speech_started": self.speech_started
        }
    
    def reset(self) -> None:
        """Reset buffer and state"""
        self.buffer = bytearray()
        self.silence_chunks = 0
        self.is_speaking = False
        self.speech_started = False
        self.energy_window.clear()
        logger.debug("AudioBuffer reset")


class ConversationState:
    """Manages conversation state with continuation support"""
    
    def __init__(self, session_id: str, business_id: int, user_id: int):
        self.session_id = session_id
        self.business_id = business_id
        self.user_id = user_id
        self.is_new_session = True
        
        # Conversation state
        self.current_transcript = ""
        self.is_agent_speaking = False
        self.agent_response_text = ""
        self.agent_response_chunks: List[str] = []
        
        # Barge-in state for continuation
        self.interrupted_response: Optional[str] = None
        self.interrupted_at_index: int = 0
        self.continuation_context: Optional[str] = None
        self.pending_work: Optional[str] = None
        
        # Timing
        self.last_activity = datetime.now()
        self.created_at = datetime.now()
        
        logger.info(f"ConversationState created for session {session_id}")
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def handle_barge_in(self, chunks_spoken: int) -> Dict[str, Any]:
        """
        Handle user interruption intelligently
        Preserves context and remaining response for continuation
        """
        if not self.is_agent_speaking or not self.agent_response_chunks:
            return {"interrupted": False}
        
        # Save interrupted state
        self.interrupted_response = " ".join(self.agent_response_chunks)
        self.interrupted_at_index = chunks_spoken
        
        # Extract what was said and what remains
        spoken_text = " ".join(self.agent_response_chunks[:chunks_spoken])
        remaining_text = " ".join(self.agent_response_chunks[chunks_spoken:])
        
        # Create continuation context
        self.continuation_context = (
            f"[Context: I was explaining something to the user. "
            f"I said: '{spoken_text}' but was interrupted. "
            f"I still need to convey: '{remaining_text}'. "
            f"Listen to the user's input carefully - if they're asking a new question, "
            f"answer it fully. If they want me to continue, resume from where I left off.]"
        )
        
        # Mark as interrupted
        self.is_agent_speaking = False
        self.pending_work = remaining_text if len(remaining_text) > 20 else None
        
        logger.info(f"Barge-in handled - Spoken: {len(spoken_text)} chars, "
                   f"Remaining: {len(remaining_text)} chars")
        
        return {
            "interrupted": True,
            "spoken_text": spoken_text,
            "remaining_text": remaining_text,
            "has_pending_work": self.pending_work is not None
        }
    
    def get_continuation_context(self) -> Optional[str]:
        """Get continuation context if available"""
        context = self.continuation_context
        # Clear after retrieval
        self.continuation_context = None
        return context
    
    def clear_continuation(self) -> None:
        """Clear continuation state"""
        self.interrupted_response = None
        self.interrupted_at_index = 0
        self.continuation_context = None
        self.pending_work = None
    
    def start_agent_response(self, full_text: str) -> None:
        """Mark that agent is starting to speak"""
        self.is_agent_speaking = True
        self.agent_response_text = full_text
        # Split into chunks for tracking
        self.agent_response_chunks = full_text.split(". ")
        self.update_activity()
    
    def end_agent_response(self) -> None:
        """Mark that agent finished speaking"""
        self.is_agent_speaking = False
        self.agent_response_text = ""
        self.agent_response_chunks = []
        self.clear_continuation()
    
    def add_transcript(self, text: str) -> None:
        """Add to current transcript"""
        self.current_transcript += f" {text}"
        self.update_activity()
    
    def get_and_clear_transcript(self) -> str:
        """Get accumulated transcript and clear it"""
        transcript = self.current_transcript.strip()
        self.current_transcript = ""
        return transcript


class VoiceConversationManager:
    """
    Orchestrates real-time voice conversations with intelligent turn detection
    Handles STT → AI Agent → TTS pipeline with barge-in support
    """
    
    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        logger.info("VoiceConversationManager initialized")
    
    async def create_session(
        self,
        session_id: str,
        business_id: int,
        user_id: int
    ) -> ConversationState:
        """Create a new conversation session"""
        state = ConversationState(session_id, business_id, user_id)
        self.sessions[session_id] = state
        self.audio_buffers[session_id] = AudioBuffer()
        
        logger.info(f"Created voice conversation session: {session_id}")
        return state
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    async def process_audio_chunk(
        self,
        session_id: str,
        audio_data: bytes
    ) -> Dict[str, Any]:
        """
        Process incoming audio chunk with VAD and silence detection
        Returns status and any detected events
        """
        state = self.get_session(session_id)
        buffer = self.audio_buffers.get(session_id)
        
        if not state or not buffer:
            return {"error": "Session not found"}
        
        # Add to buffer
        buffer.add_audio(audio_data)
        
        # Check for complete chunks and detect speech
        events = []
        chunks_for_stt = []
        
        while buffer.has_complete_chunk():
            chunk = buffer.get_chunk()
            if chunk:
                # Detect speech activity
                vad_result = buffer.detect_speech_activity(chunk)
                
                # If speech detected, collect for STT
                if vad_result["speech_started"]:
                    chunks_for_stt.append(chunk)
                
                # Check for turn end
                if vad_result["should_end_turn"]:
                    events.append({
                        "type": "turn_end",
                        "transcript": state.get_and_clear_transcript(),
                        "silence_duration": buffer.silence_duration
                    })
                    buffer.reset()
                    break
                
                # Check for barge-in (user speaking while agent is speaking)
                if state.is_agent_speaking and vad_result["is_speaking"]:
                    barge_in_result = state.handle_barge_in(chunks_spoken=0)
                    events.append({
                        "type": "barge_in",
                        **barge_in_result
                    })
        
        return {
            "status": "processing",
            "events": events,
            "audio_chunks": chunks_for_stt,
            "is_speaking": buffer.is_speaking,
            "speech_started": buffer.speech_started
        }
    
    async def handle_transcription(
        self,
        session_id: str,
        transcript: str,
        is_final: bool = False
    ) -> Dict[str, Any]:
        """Handle incoming transcription from STT"""
        state = self.get_session(session_id)
        if not state:
            return {"error": "Session not found"}
        
        state.add_transcript(transcript)
        
        if is_final:
            full_transcript = state.get_and_clear_transcript()
            return {
                "status": "transcription_complete",
                "transcript": full_transcript,
                "should_process": len(full_transcript.strip()) > 0
            }
        
        return {
            "status": "transcription_partial",
            "transcript": transcript
        }
    
    async def prepare_agent_request(
        self,
        session_id: str,
        transcript: str
    ) -> Dict[str, Any]:
        """
        Prepare request for voice agent API with continuation context
        """
        state = self.get_session(session_id)
        if not state:
            return {"error": "Session not found"}
        
        # Include continuation context if available
        continuation = state.get_continuation_context()
        
        request_payload = {
            "session_id": session_id,
            "transcript": transcript,
            "business_id": state.business_id,
            "user_id": state.user_id,
            "new_session": state.is_new_session
        }
        
        if continuation:
            request_payload["system_context"] = continuation
        
        # Mark as not new after first request
        state.is_new_session = False
        
        return request_payload
    
    async def cleanup_session(self, session_id: str) -> None:
        """Clean up session resources"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        logger.info(f"Cleaned up session: {session_id}")
    
    async def cleanup_expired_sessions(self, timeout_minutes: int = 30) -> int:
        """Clean up expired sessions, returns count of cleaned sessions"""
        expired = [
            sid for sid, state in self.sessions.items()
            if state.is_expired(timeout_minutes)
        ]
        
        for session_id in expired:
            await self.cleanup_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)


# Global instance
voice_manager = VoiceConversationManager()
