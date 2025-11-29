# This is the corrected websocket_voice_endpoint function
# Replace the entire function in voice.py with this

@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    Real-time voice conversation WebSocket endpoint
    Handles bidirectional audio streaming with STT → AI Agent → TTS pipeline
    """
    session_id = None
    
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        # Wait for initial connection message with session info
        initial_data = await websocket.receive_json()
        
        business_id = initial_data.get("business_id", 2)
        user_id = initial_data.get("user_id", 1)
        
        # Initialize voice agent session
        try:
            session_id = await session_service.create_session(business_id, user_id)
            
            # Initialize voice conversation state
            voice_manager.create_session(session_id, business_id, user_id)
            
            # Send session initialized confirmation
            await websocket.send_json({
                "type": "session_initialized",
                "session_id": session_id,
                "business_id": business_id,
                "user_id": user_id,
                "message": "Voice conversation session ready"
            })
            
            logger.info(f"Voice session initialized: {session_id}")
            
        except Exception as e:
            # Fallback: create voice session without session_service
            session_id = str(uuid.uuid4())
            voice_manager.create_session(session_id, business_id, user_id)
            await websocket.send_json({
                "type": "session_initialized",
                "session_id": session_id,
                "business_id": business_id,
                "user_id": user_id
            })
            logger.warning(f"Session service unavailable, using fallback session: {session_id}")
        
        # Initialize services
        murf_tts = MurfTTSService()
        transcription_buffer = ""
        chunks_spoken = 0
        
        # Connection heartbeat task
        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except:
                    break
        
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Main message loop
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=300.0
                )

                if "bytes" in message:
                    # Audio data from client
                    audio_data = message["bytes"]

                    # Add to transcription buffer and detect speech
                    state = voice_manager.get_session(session_id)
                    if not state:
                        continue

                    # Simple transcription using file-based approach
                    try:
                        # Convert audio to base64 for logging
                        import base64
                        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                        logger.debug(f"Received audio chunk: {len(audio_data)} bytes")

                        # For now, accumulate audio and use a simpler approach
                        # Add transcript to state (simulated - in production use real STT)
                        if len(audio_data) > 1000:  # Minimum audio threshold
                            # Send mock transcription for testing
                            test_transcript = "[Audio received - STT integration pending]"
                            await websocket.send_json({
                                "type": "transcription",
                                "text": test_transcript,
                                "is_final": False
                            })

                            state.add_transcript(test_transcript)

                    except Exception as e:
                        logger.error(f"Audio processing error: {e}")

                    # Detect turn end with simple timeout
                    # Check if we should process (after detecting silence)
                    if transcription_buffer and len(transcription_buffer) > 10:
                        await websocket.send_json({
                            "type": "processing",
                            "message": "Sia is thinking..."
                        })

                        try:
                            from app.services.nlu import parse_intent_with_session
                            from app.services.resolver import resolver_service

                            db = next(get_db_session())

                            try:
                                nlu_result = await parse_intent_with_session(
                                    transcription_buffer.strip(),
                                    session_id,
                                    business_id,
                                    user_id,
                                    db
                                )

                                response = await resolver_service.resolve_unified(
                                    nlu_result,
                                    session_id,
                                    business_id,
                                    user_id,
                                    db
                                )

                                response_text = response.get("natural_language_response", "")
                                session_complete = response.get("session_complete", False)

                                if response_text:
                                    await websocket.send_json({
                                        "type": "agent_speaking",
                                        "text": response_text
                                    })

                                    # Stream TTS audio
                                    async for audio_chunk in murf_tts.stream_speech(response_text):
                                        await websocket.send_bytes(audio_chunk)

                                    await websocket.send_json({
                                        "type": "agent_finished",
                                        "session_complete": session_complete
                                    })

                                    if session_complete:
                                        break

                            finally:
                                db.close()

                        except Exception as agent_error:
                            logger.error(f"Agent error: {agent_error}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "message": "Sia is not responding. Please try again."
                            })

                        transcription_buffer = ""

                elif "text" in message:
                    # JSON command from client
                    try:
                        data = json.loads(message["text"])
                        command = data.get("type") or data.get("command")
                        
                        if command == "stop_listening":
                            # User stopped listening manually
                            pass
                        elif command == "stop":
                            await websocket.send_json({"type": "stopped"})
                            break
                        elif command == "ping":
                            await websocket.send_json({"type": "pong"})
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message: {message['text']}")
                        continue

            except asyncio.TimeoutError:
                logger.warning(f"Session {session_id} timed out")
                await websocket.send_json({
                    "type": "timeout",
                    "message": "Session expired due to inactivity"
                })
                break

            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {session_id}")
                break

            except Exception as msg_error:
                logger.error(f"Error in message loop: {msg_error}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": "An error occurred"
                })
        
        heartbeat_task.cancel()
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    
    finally:
        if session_id:
            await voice_manager.cleanup_session(session_id)
        
        try:
            await websocket.close()
        except:
            pass
        
        logger.info(f"WebSocket connection closed: {session_id}")
