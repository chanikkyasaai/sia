"""
Quick test for transaction creation fix
"""

from app.db.session import get_db
from app.services.execution import execution_engine
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_transaction_fix():
    """Test if transaction creation works now"""

    db = next(get_db())

    # Test data
    entities = {
        "sale_amount": 100,
        "quantity": 5,
        "customer_name": "Ravi",
        "product_name": "apples"
    }

    resolved_entities = {
        "customer": {"customer_id": 4, "name": "Ravi"},
        "product": {"product_id": 2, "name": "Apples"}
    }

    try:
        result = await execution_engine.execute_intent(
            db=db,
            business_id="2",
            user_id="1",
            intent="TXN_SALE",
            entities=entities,
            resolved_entities=resolved_entities
        )

        print(f"Success: {result['success']}")
        print(f"Message: {result.get('message', 'No message')}")
        print(f"Actions: {result.get('actions_taken', [])}")

        if result['success']:
            print("✅ Transaction creation works!")
        else:
            print(f"❌ Still failing: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_transaction_fix())
