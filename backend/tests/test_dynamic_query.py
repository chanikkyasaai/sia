"""
Test cases for dynamic query generation in ExecutionEngine

Tests GPT-4 mini integration for generating and executing SQL queries
for unhandled business intelligence intents.
"""

import pytest
import asyncio
from sqlalchemy.orm import Session
from app.services.execution import execution_engine
from app.db.session import get_db
from app.db.models.transactions import Transaction
from app.db.models.customers import Customer
from app.db.models.products import Product
from app.db.models.inventory_items import InventoryItem
from datetime import datetime, date
from decimal import Decimal


class TestDynamicQueryGeneration:
    """Test dynamic query generation for business intelligence"""

    @pytest.fixture
    async def db_session(self):
        """Get database session for testing"""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    async def setup_test_data(self, db_session: Session):
        """Setup test data for dynamic queries"""
        business_id = 2

        # Create test customer
        customer = Customer(
            id=1,
            business_id=business_id,
            name="Test Customer",
            phone="1234567890",
            risk_level="LOW",
            credit=Decimal("500.00"),
            created_at=datetime.utcnow()
        )
        db_session.add(customer)

        # Create test product
        product = Product(
            id=1,
            business_id=business_id,
            name="Test Product",
            avg_sale_price=Decimal("100.00"),
            avg_cost_price=Decimal("50.00"),
            low_stock_threshold=10,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(product)

        # Create test transactions
        transactions = [
            Transaction(
                id=1,
                business_id=business_id,
                customer_id=1,
                product_id=1,
                type="SALE",
                amount=Decimal("100.00"),
                quantity=Decimal("2"),
                note="Test sale transaction",
                source="VOICE",
                created_at=datetime.utcnow()
            ),
            Transaction(
                id=2,
                business_id=business_id,
                customer_id=1,
                product_id=1,
                type="PURCHASE",
                amount=Decimal("50.00"),
                quantity=Decimal("5"),
                note="Test purchase transaction",
                source="VOICE",
                created_at=datetime.utcnow()
            )
        ]

        for transaction in transactions:
            db_session.add(transaction)

        # Create inventory item
        inventory = InventoryItem(
            id=1,
            business_id=business_id,
            product_id=1,
            quantity_on_hand=Decimal("25"),
            reorder_level=10,
            updated_at=datetime.utcnow()
        )
        db_session.add(inventory)

        try:
            db_session.commit()
            yield business_id
        finally:
            # Cleanup
            db_session.rollback()

    async def test_dynamic_query_top_customers(self, db_session: Session, setup_test_data):
        """Test Case 1: Dynamic query for top customers by transaction volume"""
        business_id = setup_test_data

        # Test intent for finding top customers
        intent = "ASK_TOP_CUSTOMERS"
        entities = {
            "metric": "transaction_volume",
            "period": "all_time",
            "limit": 5
        }

        # Execute dynamic query through execution engine
        result = await execution_engine._execute_query_intent(
            db=db_session,
            business_id=str(business_id),
            intent=intent,
            entities=entities
        )

        # Assertions
        print("\n=== Test Case 1: Top Customers Query ===")
        print(f"Intent: {intent}")
        print(f"Entities: {entities}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Actions: {result.get('actions_taken', [])}")

        if result.get('success'):
            data = result.get('data', {})
            print(f"Query Type: {data.get('query_type')}")
            print(f"Row Count: {data.get('row_count', 0)}")
            print(f"Results: {data.get('results', [])}")
            print(f"Insight: {data.get('insight')}")
        else:
            print(f"Error: {result.get('error')}")

        # Basic assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, dict), "Result should be a dictionary"

        if result.get('success'):
            assert "actions_taken" in result, "Should have actions_taken"
            assert "data" in result, "Should have data"
            assert "message" in result, "Should have message"

            data = result.get('data', {})
            assert data.get('query_type') == intent, "Should match the intent"
            assert isinstance(data.get('results', []),
                              list), "Results should be a list"

        return result

    async def test_dynamic_query_product_performance(self, db_session: Session, setup_test_data):
        """Test Case 2: Dynamic query for product performance analysis"""
        business_id = setup_test_data

        # Test intent for product performance
        intent = "ASK_PRODUCT_PERFORMANCE"
        entities = {
            "analysis_type": "sales_and_inventory",
            "time_period": "last_30_days"
        }

        # Execute dynamic query through execution engine
        result = await execution_engine._execute_query_intent(
            db=db_session,
            business_id=str(business_id),
            intent=intent,
            entities=entities
        )

        # Assertions and reporting
        print("\n=== Test Case 2: Product Performance Query ===")
        print(f"Intent: {intent}")
        print(f"Entities: {entities}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Actions: {result.get('actions_taken', [])}")

        if result.get('success'):
            data = result.get('data', {})
            print(f"Query Type: {data.get('query_type')}")
            print(f"Row Count: {data.get('row_count', 0)}")
            print(f"Results: {data.get('results', [])}")
            print(f"Insight: {data.get('insight')}")
        else:
            print(f"Error: {result.get('error')}")

        # Basic assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, dict), "Result should be a dictionary"

        if result.get('success'):
            assert "actions_taken" in result, "Should have actions_taken"
            assert "data" in result, "Should have data"
            assert "message" in result, "Should have message"

            data = result.get('data', {})
            assert data.get('query_type') == intent, "Should match the intent"
            assert isinstance(data.get('results', []),
                              list), "Results should be a list"

        return result


async def run_test_cases():
    """Run the test cases independently"""

    print("🚀 Starting Dynamic Query Generation Tests")
    print("=" * 60)

    try:
        # Get database session
        db = next(get_db())

        # Setup test data
        business_id = 2

        # Create minimal test data
        customer = Customer(
            id=1,
            business_id=business_id,
            name="John Doe",
            phone="9876543210",
            risk_level="LOW",
            credit=Decimal("1000.00"),
            created_at=datetime.utcnow()
        )
        db.merge(customer)  # Use merge to handle existing records

        product = Product(
            id=1,
            business_id=business_id,
            name="Apple iPhone",
            avg_sale_price=Decimal("50000.00"),
            avg_cost_price=Decimal("40000.00"),
            low_stock_threshold=5,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.merge(product)

        # Create transactions
        transaction1 = Transaction(
            id=1,
            business_id=business_id,
            customer_id=1,
            product_id=1,
            type="SALE",
            amount=Decimal("50000.00"),
            quantity=Decimal("1"),
            note="iPhone sale to customer",
            source="VOICE",
            created_at=datetime.utcnow()
        )
        db.merge(transaction1)

        transaction2 = Transaction(
            id=2,
            business_id=business_id,
            customer_id=1,
            product_id=1,
            type="SALE",
            amount=Decimal("25000.00"),
            quantity=Decimal("1"),
            note="Another sale transaction",
            source="VOICE",
            created_at=datetime.utcnow()
        )
        db.merge(transaction2)

        db.commit()
        print("✅ Test data setup complete")

        # Test Case 1: Top Customers Analysis
        print("\n🔍 Test Case 1: Top Customers by Revenue")
        result1 = await execution_engine._execute_query_intent(
            db=db,
            business_id=str(business_id),
            intent="ASK_TOP_CUSTOMERS_REVENUE",
            entities={
                "metric": "total_revenue",
                "limit": 10,
                "period": "all_time"
            }
        )

        print(f"   Success: {result1.get('success')}")
        print(f"   Message: {result1.get('message', 'No message')}")
        if result1.get('success'):
            data = result1.get('data', {})
            print(f"   Row Count: {data.get('row_count', 0)}")
            print(f"   Insight: {data.get('insight', 'No insight')}")
        else:
            print(f"   Error: {result1.get('error', 'Unknown error')}")

        # Test Case 2: Product Sales Performance
        print("\n🔍 Test Case 2: Product Sales Performance")
        result2 = await execution_engine._execute_query_intent(
            db=db,
            business_id=str(business_id),
            intent="ASK_PRODUCT_SALES_PERFORMANCE",
            entities={
                "analysis_type": "sales_summary",
                "include_quantity": True
            }
        )

        print(f"   Success: {result2.get('success')}")
        print(f"   Message: {result2.get('message', 'No message')}")
        if result2.get('success'):
            data = result2.get('data', {})
            print(f"   Row Count: {data.get('row_count', 0)}")
            print(f"   Insight: {data.get('insight', 'No insight')}")
        else:
            print(f"   Error: {result2.get('error', 'Unknown error')}")

        print("\n" + "=" * 60)
        print("🎉 Dynamic Query Generation Tests Complete")

        # Return results for further analysis
        return {
            "test1": result1,
            "test2": result2
        }

    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return {"error": str(e)}

    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    # Run test cases
    results = asyncio.run(run_test_cases())

    print("\n📊 Test Summary:")
    # Normalize results to a dict to avoid attribute errors if a string or other type is returned
    if isinstance(results, str):
        results = {"error": results}
    if not isinstance(results, dict):
        print(f"   ❌ Unexpected result type: {type(results).__name__}")
        results = {"error": "Unexpected result type"}

    if "error" in results:
        print(f"   ❌ Tests failed with error: {results['error']}")
    else:
        test1_success = bool(results.get("test1", {}).get("success", False))
        test2_success = bool(results.get("test2", {}).get("success", False))

        print(
            f"   Test 1 (Top Customers): {'✅ PASS' if test1_success else '❌ FAIL'}")
        print(
            f"   Test 2 (Product Performance): {'✅ PASS' if test2_success else '❌ FAIL'}")

        if test1_success and test2_success:
            print("\n🎯 All tests passed! Dynamic query generation is working correctly.")
        else:
            print(
                "\n⚠️  Some tests failed. Check the error messages above for debugging.")
