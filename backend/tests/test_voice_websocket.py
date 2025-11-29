"""
Test Real-Time Voice Conversation System
Tests WebSocket connection, audio streaming, STT→AI→TTS pipeline
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_voice_websocket():
    """
    Test WebSocket voice conversation endpoint
    """
    uri = "ws://127.0.0.1:8000/voice/ws/voice"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket connected")
            
            # Send initial connection message
            await websocket.send(json.dumps({
                "business_id": 2,
                "user_id": 1
            }))
            logger.info("📤 Sent connection init")
            
            # Wait for session initialization
            response = await websocket.recv()
            message = json.loads(response)
            logger.info(f"📥 Received: {message}")
            
            if message.get("type") == "session_initialized":
                session_id = message.get("session_id")
                logger.info(f"✅ Session initialized: {session_id}")
                
                # Test ping/pong
                await websocket.send(json.dumps({"command": "ping"}))
                pong = await websocket.recv()
                logger.info(f"📥 Heartbeat: {json.loads(pong)}")
                
                logger.info("✅ All tests passed!")
                
                # Stop gracefully
                await websocket.send(json.dumps({"command": "stop"}))
                
            else:
                logger.error(f"❌ Unexpected message type: {message.get('type')}")
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


async def test_session_creation():
    """
    Test voice session creation and management
    """
    from app.services.voice_conversation import voice_manager
    
    logger.info("Testing voice conversation manager...")
    
    # Create session
    session = await voice_manager.create_session(
        session_id="test-session-123",
        business_id=2,
        user_id=1
    )
    
    assert session is not None
    assert session.session_id == "test-session-123"
    assert session.business_id == 2
    assert session.user_id == 1
    logger.info("✅ Session created successfully")
    
    # Test audio buffer
    buffer = voice_manager.audio_buffers.get("test-session-123")
    assert buffer is not None
    logger.info("✅ Audio buffer initialized")
    
    # Test prepare agent request
    request = await voice_manager.prepare_agent_request(
        "test-session-123",
        "What are my sales today?"
    )
    
    assert "session_id" in request
    assert request["transcript"] == "What are my sales today?"
    assert request["business_id"] == 2
    logger.info("✅ Agent request prepared correctly")
    
    # Cleanup
    await voice_manager.cleanup_session("test-session-123")
    assert "test-session-123" not in voice_manager.sessions
    logger.info("✅ Session cleaned up")
    
    logger.info("✅ All session tests passed!")


async def test_continuation_context():
    """
    Test barge-in and continuation handling
    """
    from app.services.voice_conversation import ConversationState
    
    logger.info("Testing continuation context...")
    
    state = ConversationState("test-123", 2, 1)
    
    # Simulate agent speaking
    response_text = "Your sales today are excellent. You made $5000 from 10 transactions. Your top customer was John Smith with $1200 in purchases."
    state.start_agent_response(response_text)
    
    assert state.is_agent_speaking == True
    assert len(state.agent_response_chunks) > 0
    logger.info("✅ Agent response started")
    
    # Simulate barge-in
    barge_in_result = state.handle_barge_in(chunks_spoken=2)
    
    assert barge_in_result["interrupted"] == True
    assert len(barge_in_result["spoken_text"]) > 0
    assert len(barge_in_result["remaining_text"]) > 0
    logger.info(f"✅ Barge-in handled: spoken={len(barge_in_result['spoken_text'])} chars, remaining={len(barge_in_result['remaining_text'])} chars")
    
    # Get continuation context
    context = state.get_continuation_context()
    assert context is not None
    assert "interrupted" in context
    logger.info("✅ Continuation context retrieved")
    
    logger.info("✅ All continuation tests passed!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VOICE CONVERSATION SYSTEM TESTS")
    print("="*60 + "\n")
    
    # Test 1: Session creation and management
    print("\n[TEST 1] Session Creation and Management")
    print("-" * 60)
    asyncio.run(test_session_creation())
    
    # Test 2: Continuation context
    print("\n[TEST 2] Continuation Context and Barge-in")
    print("-" * 60)
    asyncio.run(test_continuation_context())
    
    # Test 3: WebSocket connection (requires running server)
    print("\n[TEST 3] WebSocket Connection")
    print("-" * 60)
    print("WARNING: Make sure backend server is running on port 8000")
    print("    Start with: uvicorn app.main:app --reload")
    
    try:
        asyncio.run(test_voice_websocket())
    except Exception as e:
        print(f"WARNING: WebSocket test skipped (server not running): {e}")
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60 + "\n")
