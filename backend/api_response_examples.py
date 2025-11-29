"""
SIA Voice Agent - API Response Format Documentation

This file shows the expected API response formats for different scenarios.
"""

# ===== SUCCESSFUL AUTO-EXECUTION =====
SUCCESSFUL_SALE_RESPONSE = {
    "reply_text": "Sale of ₹50 recorded successfully",
    "actions_taken": [
        "Created sale transaction for ₹50",
        "Updated inventory: -5 units",
        "Updated daily analytics"
    ],
    "risks": [],
    "conversation_log_id": None,
    "nlu": {
        "intent": "SALE_TRANSACTION",
        "entities": {
            "product_name": "apples",
            "customer_name": "Ravi",
            "amount": 50,
            "quantity": 5,
            "payment_method": "CASH"
        },
        "confidence": 0.95,
        "needs_clarification": False,
        "clarification_question": None,
        "language": "en"
    },
    "resolved": {
        "customer": {
            "id": "12345",
            "name": "Ravi",
            "phone": "9876543210"
        },
        "product": {
            "id": "67890",
            "name": "apples",
            "price": 10.0
        }
    },
    "snapshot": {
        "total_customers": 25,
        "total_products": 15,
        "low_stock_count": 3
    },
    "can_auto_execute": True,
    "execution_data": {
        "transaction_id": "txn_abc123",
        "amount": 50.0,
        "customer": "Ravi",
        "product": "apples",
        "quantity": 5
    },
    "session_active": False,
    "session_complete": True
}

# ===== CONFIRMATION REQUIRED =====
CONFIRMATION_REQUIRED_RESPONSE = {
    "reply_text": "This is a high-value transaction (₹15000). Please confirm: Sale of goods worth ₹15000 to Ravi?",
    "actions_taken": [],
    "risks": [],
    "conversation_log_id": None,
    "nlu": {
        "intent": "SALE_TRANSACTION",
        "entities": {
            "product_name": "goods",
            "customer_name": "Ravi",
            "amount": 15000,
            "quantity": 1
        },
        "confidence": 0.9,
        "needs_clarification": False,
        "clarification_question": None,
        "language": "en"
    },
    "resolved": {
        "customer": {
            "id": "12345",
            "name": "Ravi",
            "phone": "9876543210"
        }
    },
    "confirmation_required": True,
    "confirmation_data": {
        "reason": "HIGH_VALUE_TRANSACTION",
        "threshold": 5000,
        "amount": 15000,
        "message": "This is a high-value transaction (₹15000). Please confirm: Sale of goods worth ₹15000 to Ravi?",
        "auto_confirm": False
    },
    "session_id": "session_uuid_123",
    "session_active": True
}

# ===== MISSING INFORMATION (CLARIFICATION) =====
CLARIFICATION_NEEDED_RESPONSE = {
    "reply_text": "I understand you made a sale to Ravi. Could you please tell me: What did you sell and for how much?",
    "actions_taken": [],
    "risks": [],
    "conversation_log_id": None,
    "nlu": {
        "intent": "SALE_TRANSACTION",
        "entities": {
            "customer_name": "Ravi"
        },
        "confidence": 0.8,
        "needs_clarification": True,
        "clarification_question": "What did you sell and for how much?",
        "language": "en",
        "missing_fields": ["product_name", "amount"]
    },
    "session_id": "session_uuid_456",
    "session_active": True
}

# ===== QUERY RESPONSE =====
STOCK_INQUIRY_RESPONSE = {
    "reply_text": "apples: 45 units in stock",
    "actions_taken": [
        "Retrieved stock for apples"
    ],
    "risks": [],
    "conversation_log_id": None,
    "nlu": {
        "intent": "STOCK_INQUIRY",
        "entities": {
            "product_name": "apples"
        },
        "confidence": 0.95,
        "needs_clarification": False,
        "clarification_question": None,
        "language": "en"
    },
    "resolved": {
        "product": {
            "id": "67890",
            "name": "apples",
            "price": 10.0
        }
    },
    "snapshot": {
        "total_customers": 25,
        "total_products": 15,
        "low_stock_count": 3
    },
    "can_auto_execute": True,
    "execution_data": {
        "product": "apples",
        "stock": 45,
        "price": 10.0
    },
    "session_active": False,
    "session_complete": True
}

# ===== EXECUTION FAILED =====
EXECUTION_FAILED_RESPONSE = {
    "reply_text": "❌ Execution failed: Database error: Connection timeout",
    "actions_taken": [],
    "risks": [],
    "conversation_log_id": None,
    "nlu": {
        "intent": "SALE_TRANSACTION",
        "entities": {
            "product_name": "apples",
            "customer_name": "Ravi",
            "amount": 50,
            "quantity": 5
        },
        "confidence": 0.9,
        "needs_clarification": False,
        "clarification_question": None,
        "language": "en"
    },
    "resolved": {
        "customer": {
            "id": "12345",
            "name": "Ravi"
        },
        "product": {
            "id": "67890",
            "name": "apples"
        }
    },
    "can_auto_execute": True,
    "execution_data": {},
    "session_active": False,
    "session_complete": False,
    "error": "Database error: Connection timeout"
}

# ===== SESSION START RESPONSE =====
SESSION_START_RESPONSE = {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Voice session started successfully",
    "expires_in": 300,  # seconds
    "business_id": 1,
    "user_id": 1
}

# ===== MULTI-TURN SESSION RESPONSE =====
MULTI_TURN_SESSION_RESPONSE = {
    "reply_text": "Got it! You sold 5 apples for ₹50. Sale recorded successfully.",
    "actions_taken": [
        "Created sale transaction for ₹50",
        "Updated inventory: -5 units",
        "Updated daily analytics"
    ],
    "risks": [],
    "conversation_log_id": None,
    "nlu": {
        "intent": "SALE_TRANSACTION",
        "entities": {
            "product_name": "apples",
            "customer_name": "Ravi",  # From previous turn
            "amount": 50,
            "quantity": 5,
            "payment_method": "CASH"
        },
        "confidence": 0.92,
        "needs_clarification": False,
        "clarification_question": None,
        "language": "en",
        "session_context": {
            "previous_intent": "SALE_TRANSACTION",
            "previous_entities": {"customer_name": "Ravi"},
            "turn_number": 2
        }
    },
    "resolved": {
        "customer": {
            "id": "12345",
            "name": "Ravi",
            "phone": "9876543210"
        },
        "product": {
            "id": "67890",
            "name": "apples",
            "price": 10.0
        }
    },
    "execution_data": {
        "transaction_id": "txn_def456",
        "amount": 50.0,
        "customer": "Ravi",
        "product": "apples",
        "quantity": 5
    },
    "session_active": False,
    "session_complete": True
}


def print_response_examples():
    """Print formatted response examples"""

    print("=== SIA VOICE AGENT - API RESPONSE EXAMPLES ===\\n")

    examples = [
        ("Successful Auto-Execution", SUCCESSFUL_SALE_RESPONSE),
        ("Confirmation Required", CONFIRMATION_REQUIRED_RESPONSE),
        ("Clarification Needed", CLARIFICATION_NEEDED_RESPONSE),
        ("Query Response", STOCK_INQUIRY_RESPONSE),
        ("Execution Failed", EXECUTION_FAILED_RESPONSE),
        ("Session Start", SESSION_START_RESPONSE),
        ("Multi-turn Session", MULTI_TURN_SESSION_RESPONSE)
    ]

    for title, example in examples:
        print(f"## {title}")
        print("-" * (len(title) + 3))
        print("```json")
        import json
        print(json.dumps(example, indent=2, ensure_ascii=False))
        print("```\\n")


if __name__ == "__main__":
    print_response_examples()
