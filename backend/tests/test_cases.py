"""
Test cases for SIA Voice Agent Pipeline

This file contains sample test cases to validate the voice agent functionality.
"""

import json
import asyncio
from typing import Dict, Any

# Sample test cases for voice agent
VOICE_AGENT_TEST_CASES = [
    {
        "name": "Simple Sale Transaction",
        "transcript": "I sold 5 apples to Ravi for 50 rupees in cash",
        "expected_intent": "SALE_TRANSACTION",
        "expected_entities": {
            "product_name": "apples",
            "customer_name": "Ravi",
            "quantity": 5,
            "amount": 50,
            "payment_method": "CASH"
        },
        "should_auto_execute": True
    },
    {
        "name": "Credit Transaction",
        "transcript": "Ravi gave me 100 rupees for his pending amount",
        "expected_intent": "CREDIT_RECEIVED",
        "expected_entities": {
            "customer_name": "Ravi",
            "amount": 100
        },
        "should_auto_execute": True
    },
    {
        "name": "Stock Inquiry",
        "transcript": "How many apples do I have in stock?",
        "expected_intent": "STOCK_INQUIRY",
        "expected_entities": {
            "product_name": "apples"
        },
        "should_auto_execute": True
    },
    {
        "name": "Incomplete Sale - Missing Amount",
        "transcript": "I sold 5 apples to Ravi",
        "expected_intent": "SALE_TRANSACTION",
        "expected_entities": {
            "product_name": "apples",
            "customer_name": "Ravi",
            "quantity": 5
        },
        "should_auto_execute": False,
        "missing_fields": ["amount"]
    },
    {
        "name": "Hindi Transaction",
        "transcript": "Maine Ravi ko 5 seb 50 rupaye mein becha",
        "expected_intent": "SALE_TRANSACTION",
        "expected_entities": {
            "product_name": "seb",
            "customer_name": "Ravi",
            "quantity": 5,
            "amount": 50
        },
        "should_auto_execute": True
    },
    {
        "name": "Expense Recording",
        "transcript": "I spent 200 rupees on electricity bill",
        "expected_intent": "EXPENSE_RECORD",
        "expected_entities": {
            "amount": 200,
            "category": "UTILITIES",
            "description": "electricity bill"
        },
        "should_auto_execute": True
    },
    {
        "name": "Customer Creation",
        "transcript": "Add new customer Suresh with phone 9876543210",
        "expected_intent": "CUSTOMER_CREATE",
        "expected_entities": {
            "customer_name": "Suresh",
            "phone": "9876543210"
        },
        "should_auto_execute": True
    },
    {
        "name": "Today's Sales Inquiry",
        "transcript": "What are my total sales today?",
        "expected_intent": "SALES_INQUIRY",
        "expected_entities": {},
        "should_auto_execute": True
    },
    {
        "name": "Purchase Transaction",
        "transcript": "I bought 20 apples from wholesaler for 200 rupees",
        "expected_intent": "PURCHASE_TRANSACTION",
        "expected_entities": {
            "product_name": "apples",
            "customer_name": "wholesaler",
            "quantity": 20,
            "amount": 200
        },
        "should_auto_execute": True
    },
    {
        "name": "Credit Given",
        "transcript": "I gave 500 rupees credit to Ravi",
        "expected_intent": "CREDIT_GIVEN",
        "expected_entities": {
            "customer_name": "Ravi",
            "amount": 500
        },
        "should_auto_execute": True
    }
]

# Sample session test case for multi-turn conversation
SESSION_TEST_CASE = {
    "name": "Multi-turn Sale Transaction",
    "turns": [
        {
            "transcript": "I made a sale to Ravi",
            "expected_clarification": True,
            "expected_question": "What did you sell and for how much?"
        },
        {
            "transcript": "5 apples for 50 rupees",
            "expected_intent": "SALE_TRANSACTION",
            "expected_completion": True,
            "should_auto_execute": True
        }
    ]
}

# Validation test cases
VALIDATION_TEST_CASES = [
    {
        "name": "Large Transaction Confirmation",
        "transcript": "I sold goods worth 10000 rupees to Ravi",
        "expected_confirmation": True,
        "confirmation_reason": "HIGH_VALUE_TRANSACTION"
    },
    {
        "name": "Credit Transaction Confirmation",
        "transcript": "I gave 2000 rupees credit to new customer",
        "expected_confirmation": True,
        "confirmation_reason": "CREDIT_TO_UNKNOWN_CUSTOMER"
    },
    {
        "name": "Normal Sale Auto-Execute",
        "transcript": "I sold 2 apples to Ravi for 20 rupees",
        "expected_confirmation": False,
        "should_auto_execute": True
    }
]


def print_test_cases():
    """Print formatted test cases for manual testing"""

    print("=== SIA VOICE AGENT TEST CASES ===\\n")

    print("1. BASIC TRANSACTION TESTS")
    print("-" * 40)
    for i, test in enumerate(VOICE_AGENT_TEST_CASES[:5], 1):
        print(f"Test {i}: {test['name']}")
        print(f"Transcript: \"{test['transcript']}\"")
        print(f"Expected Intent: {test['expected_intent']}")
        print(f"Auto Execute: {test['should_auto_execute']}")
        print()

    print("2. VALIDATION TESTS")
    print("-" * 40)
    for i, test in enumerate(VALIDATION_TEST_CASES, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Transcript: \"{test['transcript']}\"")
        print(f"Needs Confirmation: {test['expected_confirmation']}")
        print()

    print("3. SESSION TEST")
    print("-" * 40)
    print(f"Test: {SESSION_TEST_CASE['name']}")
    for i, turn in enumerate(SESSION_TEST_CASE['turns'], 1):
        print(f"Turn {i}: \"{turn['transcript']}\"")
        if turn.get('expected_clarification'):
            print(f"  Expected: Clarification needed")
        if turn.get('expected_completion'):
            print(f"  Expected: Session completion")
    print()

    print("=== SAMPLE API CALLS ===\\n")

    # Sample API payloads
    print("1. Start Voice Session:")
    start_payload = {
        "business_id": 1,
        "user_id": 1
    }
    print(f"POST /voice/session/start")
    print(f"Body: {json.dumps(start_payload, indent=2)}")
    print()

    print("2. Agent Voice (without session):")
    voice_payload = {
        "business_id": 1,
        "user_id": 1,
        "transcript": "I sold 5 apples to Ravi for 50 rupees"
    }
    print(f"POST /voice/agent")
    print(f"Body: {json.dumps(voice_payload, indent=2)}")
    print()

    print("3. Agent Voice (with session):")
    session_payload = {
        "business_id": 1,
        "user_id": 1,
        "transcript": "5 apples for 50 rupees"
    }
    print(f"POST /voice/agent?session_id=<session_uuid>")
    print(f"Body: {json.dumps(session_payload, indent=2)}")
    print()


def get_sample_payloads():
    """Get sample payloads for testing different scenarios"""

    return {
        "simple_sale": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "I sold 5 apples to Ravi for 50 rupees in cash"
        },
        "incomplete_sale": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "I sold 5 apples to Ravi"
        },
        "hindi_transaction": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "Maine Ravi ko 5 seb 50 rupaye mein becha"
        },
        "stock_inquiry": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "How many apples do I have in stock?"
        },
        "expense_record": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "I spent 200 rupees on electricity bill"
        },
        "credit_received": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "Ravi gave me 100 rupees for his pending amount"
        },
        "large_transaction": {
            "business_id": 1,
            "user_id": 1,
            "transcript": "I sold goods worth 15000 rupees to Ravi"
        }
    }


if __name__ == "__main__":
    print_test_cases()
