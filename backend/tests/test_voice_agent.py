"""
Manual Testing Script for SIA Voice Agent

Run this to verify the voice agent pipeline is working correctly.
"""

from test_cases import VOICE_AGENT_TEST_CASES, get_sample_payloads
from app.services.validation import validation_service
from app.services.nlu import parse_intent
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_nlu_pipeline():
    """Test the NLU pipeline with sample inputs"""

    print("=== TESTING NLU PIPELINE ===\\n")

    # Test cases
    test_transcripts = [
        "I sold 5 apples to Ravi for 50 rupees in cash",
        "Ravi gave me 100 rupees",
        "How many apples do I have?",
        "I spent 200 on electricity",
        "Maine Ravi ko 5 seb becha"
    ]

    for i, transcript in enumerate(test_transcripts, 1):
        print(f"Test {i}: \"{transcript}\"")

        try:
            # Parse intent
            result = await parse_intent(transcript, business_id=1)

            print(f"  Intent: {result.intent}")
            print(f"  Entities: {result.entities}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Needs Clarification: {result.needs_clarification}")

            if result.needs_clarification:
                print(f"  Clarification: {result.clarification_question}")

            # Test validation
            validation_result = validation_service.validate_nlu_output(
                result.dict())
            print(f"  Validation Valid: {validation_result['is_valid']}")

            if not validation_result['is_valid']:
                print(
                    f"  Missing Fields: {validation_result['missing_fields']}")

            # Test auto-execution check
            can_auto_execute = validation_service.can_auto_execute(
                result.dict())
            print(f"  Can Auto Execute: {can_auto_execute}")

            # Test confirmation requirement
            confirmation_check = validation_service.requires_confirmation(
                result.dict(), {})
            print(
                f"  Needs Confirmation: {confirmation_check['needs_confirmation']}")

            print()

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            print()


async def test_validation_rules():
    """Test validation rules"""

    print("=== TESTING VALIDATION RULES ===\\n")

    # Test different validation scenarios
    test_cases = [
        {
            "name": "Complete Sale Transaction",
            "nlu_output": {
                "intent": "SALE_TRANSACTION",
                "entities": {
                    "product_name": "apples",
                    "customer_name": "Ravi",
                    "amount": 50,
                    "quantity": 5
                },
                "confidence": 0.9,
                "needs_clarification": False
            }
        },
        {
            "name": "Incomplete Sale Transaction",
            "nlu_output": {
                "intent": "SALE_TRANSACTION",
                "entities": {
                    "product_name": "apples",
                    "customer_name": "Ravi",
                    "quantity": 5
                    # Missing amount
                },
                "confidence": 0.8,
                "needs_clarification": False
            }
        },
        {
            "name": "High Value Transaction",
            "nlu_output": {
                "intent": "SALE_TRANSACTION",
                "entities": {
                    "product_name": "goods",
                    "customer_name": "Ravi",
                    "amount": 15000,  # High value
                    "quantity": 1
                },
                "confidence": 0.9,
                "needs_clarification": False
            }
        },
        {
            "name": "Stock Inquiry",
            "nlu_output": {
                "intent": "STOCK_INQUIRY",
                "entities": {
                    "product_name": "apples"
                },
                "confidence": 0.95,
                "needs_clarification": False
            }
        }
    ]

    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        nlu_output = test_case["nlu_output"]

        # Validation
        validation_result = validation_service.validate_nlu_output(nlu_output)
        print(f"  Valid: {validation_result['is_valid']}")
        if not validation_result['is_valid']:
            print(f"  Missing: {validation_result['missing_fields']}")

        # Auto-execution
        can_auto_execute = validation_service.can_auto_execute(nlu_output)
        print(f"  Auto Execute: {can_auto_execute}")

        # Confirmation
        confirmation_check = validation_service.requires_confirmation(
            nlu_output, {})
        print(
            f"  Needs Confirmation: {confirmation_check['needs_confirmation']}")
        if confirmation_check['needs_confirmation']:
            print(
                f"  Reason: {confirmation_check['data'].get('reason', 'Unknown')}")

        print()

# def print_api_test_commands():
#     """Print curl commands for API testing"""

#     print("=== API TESTING COMMANDS ===\\n")

#     payloads = get_sample_payloads()

#     print("1. Test Simple Sale Transaction:")
#     print("curl -X POST http://localhost:8000/voice/agent \\\\")
#     print("  -H \\"Content-Type: application/json\\" \\\\")
#     print(f"  -d '{{\\"business_id\\": 1, \\"user_id\\": 1, \\"transcript\\": \\"I sold 5 apples to Ravi for 50 rupees\\"}}'")
#     print()

#     print("2. Test Stock Inquiry:")
#     print("curl -X POST http://localhost:8000/voice/agent \\\\")
#     print("  -H \\"Content-Type: application/json\\" \\\\")
#     print(f"  -d '{{\\"business_id\\": 1, \\"user_id\\": 1, \\"transcript\\": \\"How many apples do I have in stock?\\"}}'")
#     print()

#     print("3. Test Session Start:")
#     print("curl -X POST http://localhost:8000/voice/session/start \\\\")
#     print("  -H \\"Content-Type: application/json\\" \\\\")
#     print(f"  -d '{{\\"business_id\\": 1, \\"user_id\\": 1}}'")
#     print()

#     print("4. Test Incomplete Transaction (should ask for clarification):")
#     print("curl -X POST http://localhost:8000/voice/agent \\\\")
#     print("  -H \\"Content-Type: application/json\\" \\\\")
#     print(f"  -d '{{\\"business_id\\": 1, \\"user_id\\": 1, \\"transcript\\": \\"I sold apples to Ravi\\"}}'")
#     print()

#     print("5. Test High Value Transaction (should need confirmation):")
#     print("curl -X POST http://localhost:8000/voice/agent \\\\")
#     print("  -H \\"Content-Type: application/json\\" \\\\")
#     print(f"  -d '{{\\"business_id\\": 1, \\"user_id\\": 1, \\"transcript\\": \\"I sold goods worth 15000 rupees to Ravi\\"}}'")
#     print()


async def main():
    """Run all tests"""

    print("SIA VOICE AGENT - MANUAL TESTING\\n")
    print("=" * 50)

    try:
        # Test NLU pipeline
        await test_nlu_pipeline()

        # Test validation rules
        await test_validation_rules()

        # Print API test commands
        # print_api_test_commands()

        print("\\n=== TESTING COMPLETE ===")
        print("\\nNext Steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Use the curl commands above to test the API endpoints")
        print("3. Check the logs for detailed execution flow")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
