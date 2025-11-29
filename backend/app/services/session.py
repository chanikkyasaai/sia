"""
Session management service for voice conversations with Redis ephemeral context
"""
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.cache import cache_service

logger = logging.getLogger(__name__)


class SessionService:

    def __init__(self):
        self.session_ttl = 300  # 5 minutes TTL for sessions
        # self.max_turns =   # Keep only last 4 turns

    async def create_session(self, business_id: int, user_id: int) -> str:
        """Create new session and return session_id"""
        session_id = str(uuid.uuid4())

        session_data = {
            "business_id": business_id,
            "user_id": user_id,
            "turns": [],
            "parsed_state": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True
        }

        await self._save_session(session_id, session_data)
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        if not cache_service.redis_client:
            return None

        try:
            key = f"sia:session:{session_id}"
            data = await cache_service.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")

        return None

    async def add_user_turn(self, session_id: str, transcript: str) -> Dict[str, Any]:
        """Add user turn to session context"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        # Add user turn
        user_turn = {
            "role": "user",
            "text": transcript,
            "at": datetime.now(timezone.utc).isoformat()
        }

        session["turns"].append(user_turn)

        # Keep only last N turns
        # if len(session["turns"]) > self.max_turns:
        #     session["turns"] = session["turns"][-self.max_turns:]

        await self._save_session(session_id, session)
        return session

    async def add_assistant_turn(self, session_id: str, reply_text: str, parsed_state: Dict[str, Any]) -> Dict[str, Any]:
        """Add assistant turn and update parsed state"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        # Add assistant turn
        assistant_turn = {
            "role": "assistant",
            "text": reply_text,
            "at": datetime.now(timezone.utc).isoformat()
        }

        session["turns"].append(assistant_turn)
        session["parsed_state"] = parsed_state

        # Keep only last N turns
        # if len(session["turns"]) > self.max_turns:
        #     session["turns"] = session["turns"][-self.max_turns:]

        await self._save_session(session_id, session)
        return session

    async def complete_session(self, session_id: str) -> bool:
        """Mark session as complete and schedule deletion"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session["active"] = False
        session["completed_at"] = datetime.now(timezone.utc).isoformat()

        # Save with shorter TTL (30 seconds) before deletion
        await self._save_session(session_id, session, ttl=30)
        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        if not cache_service.redis_client:
            return False

        try:
            key = f"sia:session:{session_id}"
            await cache_service.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def get_conversation_context(self, session: Dict[str, Any]) :
        """Format conversation turns for LLM context"""
        if not session.get("turns"):
            return "[]"

        formatted_turns = []
        for turn in session["turns"]:
            formatted_turns.append({
                "role": turn["role"],
                "text": turn["text"]
            })

        return json.dumps(formatted_turns, ensure_ascii=False)

    async def _save_session(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None):
        """Save session data to Redis with TTL"""
        if not cache_service.redis_client:
            raise RuntimeError("Redis client not available")

        try:
            key = f"sia:session:{session_id}"
            ttl = ttl or self.session_ttl

            await cache_service.redis_client.setex(
                key,
                ttl,
                json.dumps(session_data, default=str, ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise


# Global session service instance
session_service = SessionService()
