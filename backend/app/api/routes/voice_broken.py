from fastapi import Body
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, cast
import json
import asyncio
import uuid
import logging
from io import BytesIO
from app.services.session import session_service
from app.services.unified_analyzer import unified_analyzer
from app.services.insights_generator import InsightsGenerator

from app.api.deps import get_db_session
from app.services.stt import (
    stt_service,
    transcribe_audio,
    start_live_transcription,
    get_supported_languages as get_stt_languages
)
from app.services.tts import (
    tts_service,
    text_to_speech,
    stream_text_to_speech,
    get_available_voices,
    create_realtime_session,
    stream_for_conversation,
    realtime_tts_manager,
    MurfTTSService
)
from app.services.voice_conversation import voice_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Active WebSocket connections for real-time voice processing
active_connections: Dict[str, WebSocket] = {}
active_transcription_sessions: Dict[str, Any] = {}

# Initialize insights generator
insights_generator = InsightsGenerator()


@router.post("/agent/voice/start")
async def start_voice_session(
    payload: dict = Body(...),
    db: Session = Depends(get_db_session)
):
    """Start a new voice conversation session"""
    from app.services.session import session_service

    business_id = payload.get("business_id")
    user_id = payload.get("user_id")

    if not business_id or not user_id:
        raise HTTPException(
            status_code=400, detail="business_id and user_id are required")

    try:
        business_id = int(business_id)
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400, detail="business_id and user_id must be integers")

    session_id = await session_service.create_session(business_id, user_id)

    return {
        "session_id": session_id,
        "message": "Voice session started",
        "ttl_seconds": 300
    }


@router.post("/agent/voice")
async def agent_voice(
    session_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db_session)
):
    """
    Main agentic pipeline endpoint for voice-driven business queries/actions.
    Expects JSON: {"business_id": int, "user_id": int, "transcript": str}
    """
    from app.services.nlu import parse_intent, parse_intent_with_session
    from app.services.resolver import resolver_service

    transcript = payload.get("transcript", "")
    raw_business_id = payload.get("business_id")
    raw_user_id = payload.get("user_id")

    logger.info(f"ðŸŽ¤ Voice Agent Request - Session: {session_id}")
    logger.info(f"ðŸ“ Transcript: '{transcript}'")
    logger.info(f"ðŸ¢ Business ID: {raw_business_id}, ðŸ‘¤ User ID: {raw_user_id}")

    if raw_business_id is None:
        logger.error("âŒ Missing business_id in request")
        raise HTTPException(status_code=400, detail="business_id is required")
    if raw_user_id is None:
        logger.error("âŒ Missing user_id in request")
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        business_id = int(raw_business_id)
        user_id = int(raw_user_id)
        logger.info(
            f"âœ… Request validated - Business: {business_id}, User: {user_id}")
    except (TypeError, ValueError):
        logger.error("âŒ Invalid business_id or user_id format")
        raise HTTPException(
            status_code=400, detail="business_id and user_id must be integers")

    # Step 1: NLU parsing
    logger.info("ðŸ§  Step 1: Starting NLU processing...")
    if not session_id:
        logger.info("ðŸ”„ Using stateless NLU parsing")
        nlu_result = await parse_intent(transcript, business_id)
    else:
        logger.info(
            f"ðŸ“± Using session-based NLU parsing - Session: {session_id}")
        session_data = await session_service.get_session(session_id)
        if not session_data:
            logger.error(f"âŒ Session {session_id} not found")
            raise HTTPException(
                status_code=404, detail="Session not found")
        logger.info(
            f"âœ… Session data retrieved - History: {len(session_data.get('conversation_history', []))} messages")

        nlu_result = await parse_intent_with_session(transcript=transcript, business_id=business_id,
                                                     session_data=session_data)

    logger.info(
        f"ðŸŽ¯ NLU Results - Intent: {nlu_result.intent}, Confidence: {nlu_result.confidence}")
    logger.info(f"ðŸ“Š Entities: {nlu_result.entities}")
    logger.info(f"â“ Needs Clarification: {nlu_result.needs_clarification}")

    if nlu_result.needs_clarification:
        reply_text = nlu_result.clarification_question
        logger.info(f"â“ Clarification needed: {reply_text}")

        # If using session, add assistant turn and continue session
        if session_id:
            logger.info(f"ðŸ’¬ Adding clarification to session {session_id}")
            await session_service.add_assistant_turn(
                session_id,
                cast(str, reply_text),
                nlu_result.dict()
            )
            return {
                "reply_text": reply_text,
                "actions_taken": [],
                "risks": [],
                "conversation_log_id": None,
                "nlu": nlu_result.dict(),
                "session_id": session_id,
                "session_active": True
            }
        else:
            return {
                "reply_text": reply_text,
                "actions_taken": [],
                "risks": [],
                "conversation_log_id": None,
                "nlu": nlu_result.dict()
            }

    # Step 2: Entity resolution
    logger.info("ðŸ”— Step 2: Starting entity resolution...")
    from app.services.validation import validation_service

    resolved_entities = {}

    # Resolve customer if mentioned
    if "customer_name" in nlu_result.entities:
        customer_name = nlu_result.entities["customer_name"]
        logger.info(f"ðŸ‘¤ Resolving customer: {customer_name}")
        customer_resolution = await resolver_service.resolve_customer(
            db, business_id, customer_name
        )
        resolved_entities["customer"] = customer_resolution
        logger.info(f"âœ… Customer resolved: {customer_resolution}")

    # Resolve product if mentioned
    if "product_name" in nlu_result.entities:
        product_name = nlu_result.entities["product_name"]
        logger.info(f"ðŸ“¦ Resolving product: {product_name}")
        product_resolution = resolver_service.resolve_product(
            db, business_id, product_name
        )
        if product_resolution:
            resolved_entities["product"] = product_resolution
            logger.info(f"âœ… Product resolved: {product_resolution}")
        else:
            logger.warning(f"âš ï¸ Product '{product_name}' not found")

    # Get business snapshot
    logger.info("ðŸ“ˆ Fetching business snapshot...")
    business_snapshot = await resolver_service.get_business_snapshot(db, business_id)
    logger.info(
        f"âœ… Business snapshot retrieved: {len(business_snapshot)} metrics")

    # Step 3: Check if confirmation is required
    logger.info("âš ï¸ Step 3: Checking confirmation requirements...")
    confirmation_check = validation_service.requires_confirmation(
        nlu_result.dict(), resolved_entities)

    logger.info(
        f"ðŸ”’ Confirmation needed: {confirmation_check['needs_confirmation']}")
    if confirmation_check["needs_confirmation"]:
        reply_text = confirmation_check["data"].get(
            "message", "Please confirm this action.")
        logger.info(f"â¸ï¸ Confirmation required: {reply_text}")

        if session_id:
            await session_service.add_assistant_turn(
                session_id,
                reply_text,
                {
                    **nlu_result.dict(),
                    "confirmation_required": True,
                    "confirmation_data": confirmation_check["data"]
                }
            )
            return {
                "reply_text": reply_text,
                "actions_taken": [],
                "risks": [],
                "conversation_log_id": None,
                "nlu": nlu_result.dict(),
                "resolved": resolved_entities,
                "confirmation_required": True,
                "confirmation_data": confirmation_check["data"],
                "session_id": session_id,
                "session_active": True
            }
        else:
            return {
                "reply_text": reply_text,
                "actions_taken": [],
                "risks": [],
                "conversation_log_id": None,
                "nlu": nlu_result.dict(),
                "resolved": resolved_entities,
                "confirmation_required": True,
                "confirmation_data": confirmation_check["data"]
            }

    # Step 4: Check if auto-execution is allowed
    logger.info("âš¡ Step 4: Checking auto-execution permissions...")
    can_auto_execute = validation_service.can_auto_execute(nlu_result.dict())
    execution_data = {}  # Initialize execution_data

    logger.info(f"ðŸ”“ Auto-execution allowed: {can_auto_execute}")

    # Check if this is an analysis intent
    analysis_intents = [
        "ASK_FORECAST", "ASK_COLLECTION_PRIORITY", "ASK_CASHFLOW_HEALTH",
        "ASK_BURNRATE", "ASK_CUSTOMER_INSIGHTS", "ASK_SALES_TRENDS",
        "ASK_EXPENSE_BREAKDOWN", "ASK_CREDIT_RISK"
    ]

    logger.info(f"ðŸ” Intent classification - Intent: {nlu_result.intent}")
    logger.info(
        f"ðŸ“Š Is analysis intent: {nlu_result.intent in analysis_intents}")

    if nlu_result.intent in analysis_intents:
        try:
            logger.info("ðŸ“Š Step 5a: Starting unified analysis processing...")
            logger.info(f"ðŸŽ¯ Analysis Intent: {nlu_result.intent}")
            logger.info(f"ðŸ“‹ Analysis Entities: {nlu_result.entities}")

            # Single unified call for analysis specification AND SQL execution
            complete_analysis = await unified_analyzer.create_complete_analysis(
                db=db,
                business_id=str(business_id),
                intent=nlu_result.intent,
                entities=nlu_result.entities
            )
            logger.info("âœ… Unified analysis completed")

            analysis_spec = complete_analysis.get("analysis_spec", {})
            sql_queries = complete_analysis.get("sql_queries", [])
            validation_summary = complete_analysis.get(
                "validation_summary", {})
            query_results = complete_analysis.get("query_results", [])
            execution_summary = complete_analysis.get("execution_summary", {})
            execution_complete = complete_analysis.get(
                "execution_complete", False)

            logger.info(f"ðŸ“ˆ Analysis Results Summary:")
            logger.info(
                f"  - Analysis Type: {analysis_spec.get('analysis_type', 'Unknown')}")
            logger.info(f"  - SQL Queries Generated: {len(sql_queries)}")
            logger.info(f"  - Execution Complete: {execution_complete}")
            logger.info(f"  - Query Results: {len(query_results)} result sets")
            logger.info(
                f"  - Successful Queries: {execution_summary.get('successful_queries', 0)}")
            logger.info(
                f"  - Total Rows: {execution_summary.get('total_rows', 0)}")

            if not sql_queries or not execution_complete:
                logger.error(
                    "âŒ Analysis failed - No SQL queries generated or execution incomplete")
                reply_text = "âŒ Analysis failed: No SQL queries generated or execution incomplete"
                actions_taken = [
                    "Complete unified analysis attempted but failed to generate or execute queries"]
                execution_data = {
                    "analysis_spec": analysis_spec,
                    "validation_summary": validation_summary,
                    "execution_summary": execution_summary,
                    "error": complete_analysis.get("execution_error", "No SQL queries generated")
                }
                session_complete = True
            else:

                # Step 6: Generate business insights
                logger.info("ðŸ§  Step 6: Generating business insights...")
                if execution_summary["successful_queries"] > 0:
                    logger.info(
                        f"ðŸ“Š Processing {execution_summary['total_rows']} rows for insights")
                    insights = await insights_generator.generate_insights(
                        analysis_spec=analysis_spec,
                        query_results=query_results
                    )
                    logger.info("âœ… Insights generation completed")

                    # Create comprehensive response with insights
                    summary_text = insights.get(
                        "summary_text", "Analysis completed")
                    insight_cards = insights.get("insight_cards", [])
                    risk_flags = insights.get("risk_flags", [])
                    next_actions = insights.get("next_best_actions", [])

                    # Format insights for voice response
                    insights_summary = f"{summary_text}"
                    if insight_cards:
                        insights_summary += f" Key insights: {len(insight_cards)} cards generated."
                    if risk_flags:
                        insights_summary += f" {len(risk_flags)} risk flags identified."
                    if next_actions:
                        insights_summary += f" {len(next_actions)} action items recommended."

                    reply_text = f"ðŸ“Š {insights_summary}"
                    actions_taken = [
                        f"Analyzed {execution_summary['total_rows']} data points",
                        f"Generated {len(insight_cards)} business insights",
                        f"Identified {len(risk_flags)} risk areas",
                        f"Recommended {len(next_actions)} action items"
                    ]

                    # Include complete unified analysis data
                    execution_data = {
                        "analysis_type": analysis_spec.get("analysis_type", "unknown"),
                        "objective": analysis_spec.get("objective", "Business analysis"),
                        "execution_summary": execution_summary,
                        "insights": insights,
                        "query_results": query_results,
                        "analysis_spec": analysis_spec,
                        "validation_summary": validation_summary,
                        "unified_analysis": True,
                        "complete_analysis": True,
                        "sql_execution_integrated": True
                    }
                else:
                    # No successful queries
                    reply_text = f"âš ï¸ Analysis executed but no data found. {execution_summary.get('failed_queries', 0)} queries failed."
                    actions_taken = [
                        f"Attempted {execution_summary.get('total_queries', 0)} queries from complete unified analysis",
                        "No data retrieved for analysis",
                        "Database connectivity or data availability issue"
                    ]
                    execution_data = {
                        "analysis_type": analysis_spec.get("analysis_type", "unknown"),
                        "objective": analysis_spec.get("objective", "Business analysis"),
                        "execution_summary": execution_summary,
                        "query_results": query_results,
                        "validation_summary": validation_summary,
                        "error": "No data available for insights generation",
                        "unified_analysis": True,
                        "complete_analysis": True,
                        "sql_execution_integrated": True
                    }

                session_complete = True

        except Exception as e:
            logger.error(f"Complete unified analysis failed: {str(e)}")
            reply_text = f"âŒ Analysis failed: {str(e)}"
            actions_taken = [
                "Complete unified analysis (including SQL execution) encountered an error"]
            execution_data = {
                "error": str(e),
                "intent": nlu_result.intent,
                "unified_analysis": True,
                "complete_analysis": True,
                "failure_stage": "complete_unified_analysis"
            }
            session_complete = False

    elif can_auto_execute:
        # Execute actions automatically using execution engine
        logger.info("âš¡ Step 5b: Executing CRUD operation...")
        logger.info(f"ðŸŽ¯ CRUD Intent: {nlu_result.intent}")
        logger.info(f"ðŸ“‹ CRUD Entities: {nlu_result.entities}")
        logger.info(f"ðŸ”— Resolved Entities: {resolved_entities}")

        from app.services.execution import execution_engine

        execution_result = await execution_engine.execute_intent(
            db=db,
            business_id=str(business_id),
            user_id=str(user_id),
            intent=nlu_result.intent,
            entities=nlu_result.entities,
            resolved_entities=resolved_entities
        )

        logger.info(
            f"ðŸ’¾ CRUD Execution Result: {execution_result.get('success', False)}")
        if execution_result.get('success'):
            logger.info(
                f"âœ… CRUD Success: {execution_result.get('message', 'No message')}")
            logger.info(
                f"âš¡ Actions: {execution_result.get('actions_taken', [])}")
        else:
            logger.error(
                f"âŒ CRUD Failed: {execution_result.get('error', 'Unknown error')}")

        if execution_result["success"]:
            reply_text = execution_result["message"]
            actions_taken = execution_result["actions_taken"]
            execution_data = execution_result.get("data", {})
            session_complete = True
        else:
            reply_text = f"âŒ Execution failed: {execution_result['error']}"
            actions_taken = []
            execution_data = {}
            session_complete = False
    else:
        # Manual execution or further clarification needed
        reply_text = f"Intent: {nlu_result.intent}, Entities: {nlu_result.entities}"
        if nlu_result.dict().get("missing_fields"):
            reply_text = f"Missing info: {', '.join(nlu_result.dict().get('missing_fields', []))}"
        actions_taken = []
        session_complete = False

    response = {
        "reply_text": reply_text,
        "actions_taken": actions_taken,
        "risks": [],
        "conversation_log_id": None,
        "nlu": nlu_result.dict(),
        "resolved": resolved_entities,
        "snapshot": business_snapshot,
        "can_auto_execute": can_auto_execute
    }

    # Add execution data if available
    if execution_data:
        response["execution_data"] = execution_data

    # Handle session completion
    logger.info("ðŸ“± Step 7: Managing session state...")
    if session_id:
        if session_complete:
            logger.info(f"ðŸ Completing session {session_id}")
            await session_service.complete_session(session_id)
            response["session_active"] = False
            response["session_complete"] = True
        else:
            logger.info(
                f"ðŸ’¬ Continuing session {session_id} - Adding assistant response")
            await session_service.add_assistant_turn(
                session_id,
                reply_text,
                nlu_result.dict()
            )
            response["session_id"] = session_id
            response["session_active"] = True
    else:
        logger.info("ðŸ”„ Stateless request - No session management")

    logger.info(
        f"ðŸŽ‰ Voice Agent Processing Complete - Reply: '{reply_text[:100]}{'...' if len(reply_text) > 100 else ''}'")
    return response
# STT Endpoints


@router.post("/stt/transcribe")
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    language: str = Form("en"),
    audio_format: str = Form("wav")
):
    """
    Transcribe uploaded audio file
    Supports: wav, mp3, m4a, ogg
    Languages: en, hi, ta, te, bn, gu, kn, ml, mr, pa
    """
    try:
        # Read audio file
        audio_data = await audio_file.read()

        # Validate file size (max 10MB)
        if len(audio_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413, detail="Audio file too large (max 10MB)")

        # Transcribe audio
        result = await transcribe_audio(audio_data, language, audio_format)

        return {
            "success": result["success"],
            "transcript": result["transcript"],
            "language": language,
            "confidence": result.get("confidence", 0.0),
            "words": result.get("words", []),
            "error": result.get("error")
        }

    except Exception as e:
        logger.error(f"Audio transcription error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Transcription failed: {str(e)}")


@router.get("/stt/languages")
async def get_supported_stt_languages():
    """
    Get list of supported languages for STT
    """
    return {
        "languages": get_stt_languages(),
        "total": len(get_stt_languages())
    }


@router.websocket("/stt/realtime/{language}")
async def realtime_transcription(websocket: WebSocket, language: str = "en"):
    """
    WebSocket endpoint for real-time speech transcription
    Send binary audio data and receive transcription results
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
        # Start transcription session
        transcriber = await start_live_transcription(language)
        active_transcription_sessions[session_id] = transcriber
        active_connections[session_id] = websocket

        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "language": language,
            "message": "Real-time transcription started"
        })

        # Handle incoming audio data and outgoing transcription results
        async def handle_audio():
            try:
                while True:
                    # Receive audio data
                    audio_data = await websocket.receive_bytes()
                    await transcriber.send_audio(audio_data)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"Audio handling error: {str(e)}")

        async def handle_transcription():
            try:
                async for result in transcriber.receive_transcription():
                    await websocket.send_json({
                        "type": "transcription",
                        "transcript": result["transcript"],
                        "is_final": result["is_final"],
                        "confidence": result["confidence"],
                        "language": result["language"]
                    })
            except Exception as e:
                logger.error(f"Transcription handling error: {str(e)}")

        # Run both handlers concurrently
        await asyncio.gather(handle_audio(), handle_transcription())

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Cleanup
        if session_id in active_transcription_sessions:
            await active_transcription_sessions[session_id].close()
            del active_transcription_sessions[session_id]
        if session_id in active_connections:
            del active_connections[session_id]

# TTS Endpoints


@router.post("/tts/generate")
async def generate_speech_audio(
    text: str = Form(...),
    language: str = Form("en-IN"),
    gender: str = Form("female"),
    voice_index: int = Form(0),
    output_format: str = Form("MP3")
):
    """
    Generate speech audio from text (non-streaming)

    Parameters:
    - text: Text to convert to speech
    - language: Language code (en-IN, hi-IN, ta-IN, te-IN, etc.)
    - gender: male or female
    - voice_index: Index of voice variant (0-2)
    - output_format: MP3, WAV, OGG
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        if len(text) > 5000:  # Limit text length
            raise HTTPException(
                status_code=400, detail="Text too long (max 5000 characters)")

        result = await text_to_speech(text, language, gender, voice_index, output_format)

        if result["success"]:
            # Return audio file
            audio_stream = BytesIO(result["audio_data"])

            media_type = {
                "MP3": "audio/mpeg",
                "WAV": "audio/wav",
                "OGG": "audio/ogg"
            }.get(output_format.upper(), "audio/mpeg")

            return StreamingResponse(
                audio_stream,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename=speech.{output_format.lower()}",
                    "X-Voice-Language": language,
                    "X-Voice-Gender": gender,
                    "X-Voice-ID": result["voice_id"]
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except Exception as e:
        logger.error(f"TTS generation error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Speech generation failed: {str(e)}")


@router.post("/tts/stream")
async def stream_speech_audio(
    text: str = Form(...),
    language: str = Form("en-IN"),
    gender: str = Form("female"),
    voice_index: int = Form(0)
):
    """
    Stream speech audio in real-time (<130ms latency)
    Perfect for conversational AI responses
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Stream audio chunks
        async def audio_streamer():
            async for chunk in stream_text_to_speech(text, language, gender, voice_index):
                yield chunk

        return StreamingResponse(
            audio_streamer(),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Voice-Language": language,
                "X-Voice-Gender": gender
            }
        )

    except Exception as e:
        logger.error(f"TTS streaming error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Speech streaming failed: {str(e)}")


@router.get("/tts/voices")
async def get_tts_voices():
    """
    Get all available TTS voices by language and gender
    """
    return {
        "voices": get_available_voices(),
        "total_languages": len(get_available_voices())
    }


@router.get("/tts/voices/{language}")
async def get_voices_for_language(language: str):
    """
    Get available voices for a specific language
    """
    voices = get_available_voices()
    if language in voices:
        return {
            "language": language,
            "voices": voices[language],
            "supported": True
        }
    else:
        return {
            "language": language,
            "voices": {},
            "supported": False,
            "available_languages": list(voices.keys())
        }


@router.websocket("/tts/realtime/{session_id}")
async def realtime_tts(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time TTS
    Send text and receive audio chunks in real-time
    Perfect for conversational AI
    """
    await websocket.accept()

    try:
        # Wait for session configuration
        config_data = await websocket.receive_json()
        language = config_data.get("language", "en-IN")
        gender = config_data.get("gender", "female")
        voice_index = config_data.get("voice_index", 0)

        # Create TTS session
        await create_realtime_session(session_id, language, gender, voice_index)

        # Send confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "language": language,
            "gender": gender,
            "voice_index": voice_index
        })

        while True:
            # Receive text to convert
            message = await websocket.receive_json()

            if message.get("type") == "text":
                text = message.get("text", "")
                if text.strip():
                    # Stream audio back
                    audio_chunks = []
                    async for chunk in stream_for_conversation(session_id, text):
                        audio_chunks.append(chunk)

                    # Send audio data
                    await websocket.send_json({
                        "type": "audio",
                        "audio_data": audio_chunks,
                        "text": text
                    })

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"TTS WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"TTS WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Cleanup session
        await realtime_tts_manager.close_session(session_id)

# Combined Voice Endpoints


@router.post("/voice/conversation")
async def process_voice_conversation(
    audio_file: UploadFile = File(...),
    input_language: str = Form("en"),
    output_language: str = Form("en-IN"),
    gender: str = Form("female"),
    voice_index: int = Form(0),
    audio_format: str = Form("wav")
):
    """
    Complete voice conversation pipeline:
    1. Transcribe input audio (STT)
    2. Process with AI (you'll integrate this)
    3. Convert response to speech (TTS)

    This is perfect for voice-enabled business interactions
    """
    try:
        # Step 1: Transcribe audio
        audio_data = await audio_file.read()
        stt_result = await transcribe_audio(audio_data, input_language, audio_format)

        if not stt_result["success"]:
            raise HTTPException(
                status_code=400, detail=f"Transcription failed: {stt_result['error']}")

        transcript = stt_result["transcript"]

        # Step 2: Process with AI (placeholder - you'll integrate your AI logic here)
        # For now, just echo the transcript
        ai_response = f"I heard you say: {transcript}. How can I help you with your business?"

        # Step 3: Convert response to speech
        tts_result = await text_to_speech(ai_response, output_language, gender, voice_index)

        if not tts_result["success"]:
            raise HTTPException(
                status_code=500, detail=f"Speech generation failed: {tts_result['error']}")

        # Return both transcript and audio
        audio_stream = BytesIO(tts_result["audio_data"])

        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={
                "X-Input-Transcript": transcript,
                "X-AI-Response": ai_response,
                "X-Input-Language": input_language,
                "X-Output-Language": output_language,
                "X-Confidence": str(stt_result.get("confidence", 0.0))
            }
        )

    except Exception as e:
        logger.error(f"Voice conversation error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Voice conversation failed: {str(e)}")


@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    Real-time voice conversation WebSocket endpoint
    Handles bidirectional audio streaming with STT â†’ AI Agent â†’ TTS pipeline
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
            # Generate a unique session ID
            session_id = f"voice-{uuid.uuid4()}"
            
            # Initialize session with session service
            try:
                session_response = await session_service.initialize_session(
                    business_id=business_id,
                    user_id=user_id
                )
                session_id = session_response.get("session_id", session_id)
            except Exception as session_error:
                logger.warning(f"Session service initialization failed, using generated ID: {session_error}")
            
            # Create voice conversation state
            await voice_manager.create_session(session_id, business_id, user_id)
            
            await websocket.send_json({
                "type": "session_initialized",
                "session_id": session_id,
                "status": "ready"
            })
            
            logger.info(f"Voice session initialized: {session_id}")
            
        except Exception as e:
            logger.error(f"Session initialization failed: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": "Failed to initialize session"
            })
            return
        
        # Initialize services
        murf_tts = MurfTTSService()
        transcription_buffer = ""
        chunks_spoken = 0
        
        # Connection heartbeat task
        async def heartbeat():
            try:
                while True:
                    await asyncio.sleep(30)
                    await websocket.send_json({"type": "heartbeat"})
            except Exception:
                pass
        
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

                    elif "text" in message:`n                    # JSON command from client`n                    try:`n                        data = json.loads(message["text"])`n                        command = data.get("type") or data.get("command")`n                        `n                        if command == "stop_listening":
                        # User stopped listening manually
                        pass
                    elif command == "stop":
                        await websocket.send_json({"type": "stopped"})
                        break
                    elif command == "ping":
                        await websocket.send_json({"type": "pong"})                                    `n                    except json.JSONDecodeError:`n                        logger.error(f"Invalid JSON message: {message['text']}")`n                        continue`n`n            except asyncio.TimeoutError:
                logger.warning(f"Session {session_id} timed out")
                await websocket.send_json({
                    "type": "timeout",
                    "message": "Session expired due to inactivity"
                })
                break
            
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {session_id}")
                break
            
            except Exception as e:
                logger.error(f"Error in message loop: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": "An error occurred"
                    })
                except:
                    break
        
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


@router.get("/voice/health")
async def voice_services_health():
    """
    Health check for voice services
    """
    return {
        "stt_service": "ready",
        "tts_service": "ready",
        "unified_analyzer": "ready",
        "insights_generator": "ready",
        "supported_stt_languages": list(get_stt_languages().keys()),
        "supported_tts_languages": list(get_available_voices().keys()),
        "supported_analysis_intents": [
            "ASK_FORECAST", "ASK_COLLECTION_PRIORITY", "ASK_CASHFLOW_HEALTH",
            "ASK_INVENTORY_BURNRATE", "ASK_CUSTOMER_INSIGHTS", "ASK_SALES_TRENDS",
            "ASK_EXPENSE_BREAKDOWN", "ASK_CREDIT_RISK"
        ],
        "optimization": "complete_unified_analysis_with_sql_execution",
        "architecture": "single_llm_call_with_integrated_sql_executor",
        "performance_benefits": "reduced_api_calls_and_improved_consistency",
        "active_connections": len(active_connections),
        "active_transcription_sessions": len(active_transcription_sessions)
    }

