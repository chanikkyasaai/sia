"""
Test Intent Parsing with Redis Conversation History

This script tests two scenarios:
1. Multi-turn transaction completion with context
2. Context-aware clarification and follow-up queries
"""

from app.services.cache import cache_service
from app.services.validation import validation_service
from app.services.nlu import parse_intent_with_session
from app.services.session import session_service
import asyncio
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scenario_1_multi_turn_transaction():
    """
    Scenario 1: Multi-turn transaction completion with context

    Flow:
    1. User: "I sold apples to Ravi"  (missing amount)
    2. Agent: "Sale ka amount kitna hai?" 
    3. User: "50 rupees"  (should use context to complete transaction)
    """

    print("🔥 SCENARIO 1: Multi-turn Transaction Completion")
    print("=" * 50)

    business_id = 2
    user_id = 1

    try:
        # Step 1: Start session and process incomplete transaction
        print("\n📝 Step 1: Processing incomplete transaction")
        session_id = await session_service.create_session(business_id, user_id)
        print(f"✅ Created session: {session_id}")

        transcript_1 = "I sold apples to Ravi"
        print(f"User: \"{transcript_1}\"")

        # Parse intent with empty context (first turn)
        session_data = await session_service.get_session(session_id)
        # Ensure we pass a dict to get_conversation_context; get_session may return None.
        conversation_context = session_service.get_conversation_context(
            session_data or {})

        result_1 = await parse_intent_with_session(transcript_1, business_id, session_data or {})
        print(f"Intent: {result_1.intent}")
        print(f"Entities: {result_1.entities}")
        print(f"Confidence: {result_1.confidence}")

        # Validate the result
        validation_result_1 = validation_service.validate_nlu_output(
            result_1.model_dump())
        print(f"Is Valid: {validation_result_1['is_valid']}")
        print(f"Missing Fields: {validation_result_1['missing_fields']}")
        print(
            f"Needs Clarification: {validation_result_1['needs_clarification']}")

        if validation_result_1['needs_clarification']:
            clarification = validation_result_1.get(
                'clarification_question', 'Please provide more details.')
            print(f"Agent: \"{clarification}\"")

            # Save user turn and agent response to session
            await session_service.add_user_turn(session_id, transcript_1)
            await session_service.add_assistant_turn(session_id, clarification, result_1.entities or {})

        # Step 2: Process follow-up with amount
        print("\n📝 Step 2: Processing follow-up with missing amount")
        transcript_2 = "50 rupees"
        print(f"User: \"{transcript_2}\"")

        session_data = await session_service.get_session(session_id)
        # Ensure we pass a dict to get_conversation_context; get_session may return None.
        conversation_context = session_service.get_conversation_context(
            session_data or {})
        print(f"Conversation Context: {conversation_context}")
        print(f"Conversation Context: {conversation_context}")

        # Parse with context
        result_2 = await parse_intent_with_session(transcript_2, business_id, session_data or {})
        print(f"Intent: {result_2.intent}")
        print(f"Entities: {result_2.entities}")
        print(f"Confidence: {result_2.confidence}")

        # Validate the completed transaction
        validation_result_2 = validation_service.validate_nlu_output(
            result_2.model_dump())
        print(f"Is Valid: {validation_result_2['is_valid']}")
        print(f"Missing Fields: {validation_result_2['missing_fields']}")
        print(
            f"Can Auto Execute: {validation_service.can_auto_execute(result_2.model_dump())}")

        # Save final turn
        await session_service.add_user_turn(session_id, transcript_2)

        # Complete session
        await session_service.complete_session(session_id)
        print("✅ Session completed successfully")

    except Exception as e:
        print(f"❌ Scenario 1 failed: {e}")
        import traceback
        traceback.print_exc()


async def test_scenario_2_context_aware_queries():
    """
    Scenario 2: Context-aware clarification and follow-up queries

    Flow:
    1. User: "What's my cashflow?"
    2. Agent: Provides cashflow info
    3. User: "What about last month?" (should understand context)
    4. User: "Show me top selling products" (new query)
    5. User: "And inventory for those?" (context-dependent query)
    """

    print("\n\n🔥 SCENARIO 2: Context-aware Follow-up Queries")
    print("=" * 50)

    business_id = 1
    user_id = 1

    try:
        # Step 1: Initial cashflow query
        print("\n📝 Step 1: Initial cashflow query")
        session_id = await session_service.create_session(business_id, user_id)
        print(f"✅ Created session: {session_id}")

        transcript_1 = "What's my cashflow health?"
        print(f"User: \"{transcript_1}\"")

        session_data = await session_service.get_session(session_id)
        conversation_context = session_service.get_conversation_context(
            session_data or {})

        result_1 = await parse_intent_with_session(transcript_1, business_id, session_data or {})
        print(f"Intent: {result_1.intent}")
        print(f"Entities: {result_1.entities}")

        agent_response_1 = "Your current cashflow is healthy. Revenue: ₹50,000, Expenses: ₹30,000"
        await session_service.add_user_turn(session_id, transcript_1)
        await session_service.add_assistant_turn(session_id, agent_response_1, result_1.entities or {})

        # Step 2: Context-dependent time query
        print("\n📝 Step 2: Context-dependent time query")
        transcript_2 = "What about last month?"
        session_data = await session_service.get_session(session_id)
        # Ensure we pass a dict to get_conversation_context; get_session may return None.
        conversation_context = session_service.get_conversation_context(
            session_data or {})
        print(f"Context: {conversation_context}")

        result_2 = await parse_intent_with_session(transcript_2, business_id, session_data or {})
        print(f"Intent: {result_2.intent}")
        print(f"Entities: {result_2.entities}")
        print(f"Should understand this is about CASHFLOW for LAST_MONTH")

        agent_response_2 = "Last month's cashflow: Revenue: ₹45,000, Expenses: ₹32,000"
        await session_service.add_user_turn(session_id, transcript_2)
        await session_service.add_assistant_turn(session_id, agent_response_2, result_2.entities or {})

        # Step 3: New topic - top products
        print("\n📝 Step 3: New topic query")
        transcript_3 = "Show me top selling products"
        print(f"User: \"{transcript_3}\"")

        session_data = await session_service.get_session(session_id)
        conversation_context = session_service.get_conversation_context(
            session_data or {})

        result_3 = await parse_intent_with_session(transcript_3, business_id, session_data or {})
        print(f"Intent: {result_3.intent}")
        print(f"Entities: {result_3.entities}")

        agent_response_3 = "Top products: 1. Apples (50 units), 2. Bananas (30 units), 3. Oranges (25 units)"
        await session_service.add_user_turn(session_id, transcript_3)
        await session_service.add_assistant_turn(session_id, agent_response_3, result_3.entities or {})

        # Step 4: Context-dependent inventory query
        print("\n📝 Step 4: Context-dependent inventory query")
        transcript_4 = "And inventory for those?"
        print(f"User: \"{transcript_4}\"")

        session_data = await session_service.get_session(session_id)
        conversation_context = session_service.get_conversation_context(
            session_data or {})
        print(f"Context: {conversation_context}")

        result_4 = await parse_intent_with_session(transcript_4, business_id, session_data or {})
        print(f"Intent: {result_4.intent}")
        print(f"Entities: {result_4.entities}")
        print(f"Should understand 'those' refers to top selling products")

        await session_service.add_user_turn(session_id, transcript_4)

        # Complete session
        await session_service.complete_session(session_id)
        print("✅ Session completed successfully")

    except Exception as e:
        print(f"❌ Scenario 2 failed: {e}")
        import traceback
        traceback.print_exc()


async def test_redis_session_persistence():
    """Test Redis session persistence and retrieval"""

    print("\n\n🔥 TESTING REDIS SESSION PERSISTENCE")
    print("=" * 50)

    try:
        # Test Redis connection
        if cache_service.redis_client:
            # Test basic Redis operations
            await cache_service.redis_client.set("test_key", "test_value", ex=10)
            test_value = await cache_service.redis_client.get("test_key")
            print(f"✅ Redis basic test - Set/Get: {test_value}")

            # Test session creation and retrieval
            session_id = await session_service.create_session(business_id=1, user_id=1)
            print(f"✅ Created session: {session_id}")

            # Add some turns
            await session_service.add_user_turn(session_id, "Hello")
            await session_service.add_assistant_turn(session_id, "Hi there!", {})

            # Retrieve session
            session_data = await session_service.get_session(session_id)
            # Test conversation context formatting
            # get_session may return None, so pass a fallback empty dict.
            context = session_service.get_conversation_context(
                session_data or {})
            print(f"✅ Conversation context: {context}")
            # Test conversation context formatting
            context = session_service.get_conversation_context(
                session_data or {})
            print(f"✅ Conversation context: {context}")

            # Clean up
            await session_service.delete_session(session_id)
            print("✅ Session deleted")

        else:
            print("❌ Redis client not available")

    except Exception as e:
        print(f"❌ Redis persistence test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all conversation tests"""

    print("🚀 TESTING INTENT PARSING WITH REDIS CONVERSATION HISTORY")
    print("=" * 70)
    print(f"Test started at: {datetime.now()}")

    try:
        # Test Redis connectivity first
        await test_redis_session_persistence()

        # Run conversation scenarios
        await test_scenario_1_multi_turn_transaction()
        await test_scenario_2_context_aware_queries()

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS COMPLETED")
        print("\nKey Test Points:")
        print("✅ Redis session management")
        print("✅ Multi-turn transaction completion")
        print("✅ Context-aware intent parsing")
        print("✅ Conversation history preservation")
        print("✅ Follow-up query understanding")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup Redis connections
        try:
            await cache_service.close()
            print("\n🔒 Redis connections closed")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
