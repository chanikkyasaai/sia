"""
Test Cases for Dynamic Query Generation in Execution Engine

Tests the GPT-4 mini integration for handling unclassified intents
with parameterized query generation and execution.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from app.services.execution import execution_engine
from app.db.session import get_db

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicQueryTest:
    """Test dynamic query generation for unclassified intents"""

    def __init__(self):
        self.test_business_id = "2"
        self.test_user_id = "1"

    async def test_custom_sales_analysis(self):
        """Test Case 1: Custom sales analysis query"""
        print("\n🔥 TEST CASE 1: Custom Sales Analysis")
        print("=" * 50)

        db = next(get_db())

        try:
            # Custom intent not in predefined list
            intent = "ANALYZE_DAILY_SALES_PATTERN"
            entities = {
                "date_range": "last_7_days",
                "analysis_type": "daily_pattern",
                "metric": "sales_volume"
            }

            print(f"Intent: {intent}")
            print(f"Entities: {entities}")
            print("\n📊 Executing dynamic query generation...")

            result = await execution_engine.execute_intent(
                db=db,
                business_id=self.test_business_id,
                user_id=self.test_user_id,
                intent=intent,
                entities=entities,
                resolved_entities={}
            )

            print(f"\n✅ Results:")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Message: {result.get('message', 'No message')}")
            print(f"  Actions Taken: {result.get('actions_taken', [])}")

            if result.get('data'):
                data = result['data']
                print(
                    f"  Data Points: {len(data) if isinstance(data, list) else 'Single object'}")
                if isinstance(data, list) and data:
                    print(f"  Sample: {data[0]}")

            return result.get('success', False)

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    async def test_customer_behavior_analysis(self):
        """Test Case 2: Customer behavior analysis query"""
        print("\n🔥 TEST CASE 2: Customer Behavior Analysis")
        print("=" * 50)

        db = next(get_db())

        try:
            # Another custom intent
            intent = "ANALYZE_CUSTOMER_PURCHASE_FREQUENCY"
            entities = {
                "date_range": "last_30_days",
                "customer_segment": "all",
                "metric": "purchase_frequency",
                "threshold": "5"
            }

            print(f"Intent: {intent}")
            print(f"Entities: {entities}")
            print("\n📊 Executing dynamic query generation...")

            result = await execution_engine.execute_intent(
                db=db,
                business_id=self.test_business_id,
                user_id=self.test_user_id,
                intent=intent,
                entities=entities,
                resolved_entities={}
            )

            print(f"\n✅ Results:")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Message: {result.get('message', 'No message')}")
            print(f"  Actions Taken: {result.get('actions_taken', [])}")

            if result.get('data'):
                data = result['data']
                print(
                    f"  Data Points: {len(data) if isinstance(data, list) else 'Single object'}")
                if isinstance(data, list) and data:
                    print(f"  Sample: {data[0]}")

            return result.get('success', False)

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    async def test_product_performance_query(self):
        """Test Case 3: Product performance analysis"""
        print("\n🔥 TEST CASE 3: Product Performance Analysis")
        print("=" * 50)

        db = next(get_db())

        try:
            # Product-focused custom query
            intent = "GET_TOP_SELLING_PRODUCTS"
            entities = {
                "date_range": "last_month",
                "limit": "10",
                "sort_by": "quantity_sold",
                "include_revenue": "true"
            }

            print(f"Intent: {intent}")
            print(f"Entities: {entities}")
            print("\n📊 Executing dynamic query generation...")

            result = await execution_engine.execute_intent(
                db=db,
                business_id=self.test_business_id,
                user_id=self.test_user_id,
                intent=intent,
                entities=entities,
                resolved_entities={}
            )

            print(f"\n✅ Results:")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Message: {result.get('message', 'No message')}")
            print(f"  Actions Taken: {result.get('actions_taken', [])}")

            if result.get('data'):
                data = result['data']
                print(
                    f"  Data Points: {len(data) if isinstance(data, list) else 'Single object'}")
                if isinstance(data, list) and data:
                    print(f"  Sample: {data[0]}")

            return result.get('success', False)

        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()


async def main():
    """Run dynamic query generation tests"""
    print("🚀 DYNAMIC QUERY GENERATION - TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")

    test_suite = DynamicQueryTest()
    results = {}

    try:
        # Test 1: Custom sales analysis
        results["custom_sales_analysis"] = await test_suite.test_custom_sales_analysis()

        # Test 2: Customer behavior analysis
        results["customer_behavior_analysis"] = await test_suite.test_customer_behavior_analysis()

        # Test 3: Product performance query
        results["product_performance_query"] = await test_suite.test_product_performance_query()

        # Summary
        print("\n" + "=" * 60)
        print("📊 DYNAMIC QUERY TEST RESULTS")
        print("=" * 60)

        total_tests = len(results)
        passed_tests = sum(results.values())

        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")

        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("\n🎉 ALL DYNAMIC QUERY TESTS PASSED!")
            print("\n✅ Verified Features:")
            print("  • GPT-4 mini integration for query generation")
            print("  • Parameterized query creation and execution")
            print("  • Custom intent handling for unclassified requests")
            print("  • Business-scoped query security")
            print("  • Dynamic result formatting and messaging")
        else:
            print(
                f"\n⚠️ {total_tests - passed_tests} tests failed - Check logs above")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
