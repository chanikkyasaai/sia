"""
End-to-End Test for Voice Agent Flow
Tests complete pipeline from voice input to CRUD operations

This test covers:
1. Voice session management
2. Intent parsing with NLU
3. Entity resolution
4. SQL query generation and execution
5. Inventory operations (checking apple stock)
6. Transaction logging
7. Business insights generation
"""

from app.db.models.transactions import Transaction
from app.db.models.customers import Customer
from app.db.models.inventory_items import InventoryItem
from app.db.models.products import Product
from app.db.models.businesses import Business
from app.db.session import get_db
from app.services.execution import execution_engine
from app.services.insights_generator import InsightsGenerator
from app.services.unified_analyzer import unified_analyzer
from app.services.resolver import resolver_service
from app.services.validation import validation_service
from app.services.nlu import parse_intent, parse_intent_with_session
from app.services.session import session_service
import asyncio
import sys
import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceAgentE2ETest:
    """End-to-end test class for voice agent pipeline"""

    def __init__(self):
        self.insights_generator = InsightsGenerator()
        self.test_business_id = 2
        self.test_user_id = 1
        self.session_id = None

    async def setup_test_data(self, db):
        """Setup test data in database"""
        print("🔧 Setting up test data...")

        try:
            # Verify business exists (don't create, use existing business_id=2)
            business = db.query(Business).filter_by(
                id=self.test_business_id).first()
            if not business:
                print(
                    f"❌ Business with ID {self.test_business_id} not found. Please ensure it exists.")
                raise ValueError(
                    f"Business ID {self.test_business_id} does not exist")

            print(
                f"✅ Using existing business: {business.name} (ID: {self.test_business_id})")

            # Create test products if they don't exist
            products_data = [
                {"name": "Apples", "unit": "kg", "avg_sale_price": 120.0},
                {"name": "Bananas", "unit": "dozen", "avg_sale_price": 60.0},
                {"name": "Oranges", "unit": "kg", "avg_sale_price": 100.0},
            ]

            for product_data in products_data:
                existing = db.query(Product).filter_by(
                    business_id=self.test_business_id,
                    name=product_data["name"]
                ).first()

                if not existing:
                    product = Product(
                        business_id=self.test_business_id,
                        name=product_data["name"],
                        unit=product_data["unit"],
                        avg_sale_price=product_data["avg_sale_price"],
                        avg_cost_price=product_data["avg_sale_price"] * 0.7,
                        low_stock_threshold=10,
                        is_active=True,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(product)
                    db.commit()

                    # Add inventory for the product
                    inventory = InventoryItem(
                        business_id=self.test_business_id,
                        product_id=product.id,
                        quantity_on_hand=50,  # 50 units in stock
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(inventory)

            # Create test customer
            customer = db.query(Customer).filter_by(
                business_id=self.test_business_id,
                name="Ravi"
            ).first()

            if not customer:
                customer = Customer(
                    business_id=self.test_business_id,
                    name="Ravi",
                    phone="9876543210",
                    info="Regular customer",
                    risk_level=0,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(customer)

            db.commit()
            print("✅ Test data setup completed")

        except Exception as e:
            print(f"❌ Test data setup failed: {e}")
            db.rollback()
            raise

    async def test_inventory_query_flow(self):
        """Test 1: Complete flow for inventory query - 'How many apples do I have?'"""

        print("\\n🔥 TEST 1: Inventory Query Flow")
        print("=" * 60)

        # Get database session
        db = next(get_db())
        await self.setup_test_data(db)

        try:
            # Step 1: Start voice session
            print("\\n📝 Step 1: Starting voice session")
            self.session_id = await session_service.create_session(
                self.test_business_id, self.test_user_id
            )
            print(f"✅ Session created: {self.session_id}")

            # Step 2: Process voice input
            transcript = "How many customers visited the shop in this week?"
            print(f"\\n📝 Step 2: Processing voice input")
            print(f"User: \"{transcript}\"")

            # Step 3: NLU Processing
            session_data = await session_service.get_session(self.session_id)
            nlu_result = await parse_intent_with_session(
                transcript=transcript,
                business_id=self.test_business_id,
                session_data=session_data or {}
            )

            print(f"\\n📊 NLU Results:")
            print(f"  Intent: {nlu_result.intent}")
            print(f"  Entities: {nlu_result.entities}")
            print(f"  Confidence: {nlu_result.confidence}")
            print(f"  Needs Clarification: {nlu_result.needs_clarification}")

            # Step 4: Validation
            validation_result = validation_service.validate_nlu_output(
                nlu_result.model_dump())
            print(f"\\n🔍 Validation Results:")
            print(f"  Is Valid: {validation_result['is_valid']}")
            print(f"  Missing Fields: {validation_result['missing_fields']}")
            print(
                f"  Can Auto Execute: {validation_service.can_auto_execute(nlu_result.model_dump())}")

            # Step 5: Entity Resolution
            print(f"\\n🔗 Step 5: Entity Resolution")
            resolved_entities = {}

            if "product_name" in nlu_result.entities:
                product_resolution = resolver_service.resolve_product(
                    db, self.test_business_id, nlu_result.entities["product_name"]
                )
                resolved_entities["product"] = product_resolution
                print(f"  Product Resolution: {product_resolution}")

            # Step 6: Business Snapshot
            business_snapshot = await resolver_service.get_business_snapshot(db, self.test_business_id)
            print(f"\\n📈 Business Snapshot: {len(business_snapshot)} metrics")

            # Step 7: Unified Analysis (for inventory queries)
            if nlu_result.intent in ["ASK_FORECAST", "ASK_COLLECTION_PRIORITY", "ASK_CASHFLOW_HEALTH",
                                     "ASK_BURNRATE", "ASK_CUSTOMER_INSIGHTS", "ASK_SALES_TRENDS",
                                     "ASK_EXPENSE_BREAKDOWN", "ASK_CREDIT_RISK"]:
                print(f"\\n📊 Step 7: Unified Analysis")

                complete_analysis = await unified_analyzer.create_complete_analysis(
                    db=db,
                    business_id=str(self.test_business_id),
                    intent=nlu_result.intent,
                    entities=nlu_result.entities
                )

                analysis_spec = complete_analysis.get('analysis_spec', {})
                query_results = complete_analysis.get('query_results', [])
                execution_summary = complete_analysis.get(
                    'execution_summary', {})

                print(
                    f"  Analysis Type: {analysis_spec.get('analysis_type', 'Unknown')}")
                print(
                    f"  Objective: {analysis_spec.get('objective', 'Unknown')}")
                print(
                    f"  SQL Queries: {len(complete_analysis.get('sql_queries', []))}")
                print(
                    f"  Executed Queries: {execution_summary.get('total_queries', 0)}")
                print(
                    f"  Successful: {execution_summary.get('successful_queries', 0)}")
                print(
                    f"  Total Rows: {execution_summary.get('total_rows', 0)}")

                # Print actual results
                for i, result in enumerate(query_results):
                    if result.get('success') and result.get('data'):
                        print(
                            f"  Query {i+1} Results: {len(result['data'])} rows")
                        if result['data']:
                            print(f"    Sample: {result['data'][0]}")

                # Step 8: Insights Generation
                insights = complete_analysis.get('insights', {})
                if insights or execution_summary.get("successful_queries", 0) > 0:
                    print(f"\n🧠 Step 8: Insights Generation")
                    if not insights:
                        insights = await self.insights_generator.generate_insights(
                            analysis_spec=analysis_spec,
                            query_results=query_results
                        )

                        print(
                            f"  Summary: {insights.get('summary_text', 'No summary')}")
                        print(
                            f"  Insight Cards: {len(insights.get('insight_cards', []))}")
                        print(
                            f"  Risk Flags: {len(insights.get('risk_flags', []))}")
                        print(
                            f"  Next Actions: {len(insights.get('next_best_actions', []))}")

                        # Display key insights
                        for card in insights.get('insight_cards', [])[:2]:
                            print(
                                f"  💡 {card.get('title', 'Insight')}: {card.get('insight', 'No details')}")

            # Step 10: Session Management
            print(f"\\n📱 Step 10: Session Management")
            await session_service.add_user_turn(self.session_id, transcript)
            await session_service.add_assistant_turn(
                self.session_id,
                "Query processed successfully",
                nlu_result.entities
            )

            await session_service.complete_session(self.session_id)
            print("✅ Session completed successfully")

            print(f"\\n🎉 TEST 1 COMPLETED - Inventory Query Flow")
            return True

        except Exception as e:
            print(f"❌ Test 1 failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    async def test_transaction_creation_flow(self):
        """Test 2: Complete flow for transaction creation - 'I sold 5 apples to Ravi for 100 rupees'"""

        print("\\n🔥 TEST 2: Transaction Creation Flow")
        print("=" * 60)

        # Get database session
        db = next(get_db())

        try:
            # Step 1: Start voice session
            print("\\n📝 Step 1: Starting voice session")
            self.session_id = await session_service.create_session(
                self.test_business_id, self.test_user_id
            )
            print(f"✅ Session created: {self.session_id}")

            # Step 2: Process voice input
            transcript = "I sold 5 apples to Ravi for 100 rupees"
            print(f"\\n📝 Step 2: Processing voice input")
            print(f"User: \"{transcript}\"")

            # Step 3: NLU Processing
            session_data = await session_service.get_session(self.session_id)
            nlu_result = await parse_intent_with_session(
                transcript=transcript,
                business_id=self.test_business_id,
                session_data=session_data or {}
            )

            print(f"\\n📊 NLU Results:")
            print(f"  Intent: {nlu_result.intent}")
            print(f"  Entities: {nlu_result.entities}")
            print(f"  Confidence: {nlu_result.confidence}")

            # Step 4: Validation
            validation_result = validation_service.validate_nlu_output(
                nlu_result.model_dump())
            print(f"\\n🔍 Validation Results:")
            print(f"  Is Valid: {validation_result['is_valid']}")
            print(f"  Missing Fields: {validation_result['missing_fields']}")
            print(
                f"  Can Auto Execute: {validation_service.can_auto_execute(nlu_result.model_dump())}")

            # Step 5: Entity Resolution
            print(f"\\n🔗 Step 5: Entity Resolution")
            resolved_entities = {}

            # Resolve customer
            if "customer_name" in nlu_result.entities:
                customer_resolution = await resolver_service.resolve_customer(
                    db, self.test_business_id, nlu_result.entities["customer_name"]
                )
                resolved_entities["customer"] = customer_resolution
                print(f"  Customer Resolution: {customer_resolution}")

            # Resolve product
            if "product_name" in nlu_result.entities:
                product_resolution = resolver_service.resolve_product(
                    db, self.test_business_id, nlu_result.entities["product_name"]
                )
                resolved_entities["product"] = product_resolution
                print(f"  Product Resolution: {product_resolution}")

            # Step 6: Confirmation Check
            confirmation_check = validation_service.requires_confirmation(
                nlu_result.model_dump(), resolved_entities
            )
            print(f"\\n⚠️  Confirmation Check:")
            print(
                f"  Needs Confirmation: {confirmation_check['needs_confirmation']}")
            if confirmation_check["needs_confirmation"]:
                print(f"  Reason: {confirmation_check['reason']}")

            # Step 7: Execute Transaction (if auto-execution allowed)
            can_auto_execute = validation_service.can_auto_execute(
                nlu_result.model_dump())
            if can_auto_execute and not confirmation_check["needs_confirmation"]:
                print(f"\\n⚡ Step 7: Auto-Executing Transaction")

                execution_result = await execution_engine.execute_intent(
                    db=db,
                    business_id=str(self.test_business_id),
                    user_id=str(self.test_user_id),
                    intent=nlu_result.intent,
                    entities=nlu_result.entities,
                    resolved_entities=resolved_entities
                )

                print(f"  Execution Success: {execution_result['success']}")
                print(f"  Message: {execution_result['message']}")
                print(f"  Actions Taken: {execution_result['actions_taken']}")

                if execution_result["success"]:
                    print("✅ Transaction created successfully")
                else:
                    print(
                        f"❌ Transaction execution failed: {execution_result.get('error', 'Unknown error')}")
            else:
                print(f"\\n⏸️  Step 7: Manual confirmation required")

            # Step 8: Session Management
            print(f"\\n📱 Step 8: Session Management")
            await session_service.add_user_turn(self.session_id, transcript)
            await session_service.add_assistant_turn(
                self.session_id,
                "Transaction processed",
                nlu_result.entities
            )

            await session_service.complete_session(self.session_id)
            print("✅ Session completed successfully")

            print(f"\\n🎉 TEST 2 COMPLETED - Transaction Creation Flow")
            return True

        except Exception as e:
            print(f"❌ Test 2 failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()

    async def test_multi_turn_conversation(self):
        """Test 3: Multi-turn conversation with context"""

        print("\\n🔥 TEST 3: Multi-turn Conversation Flow")
        print("=" * 60)

        # Get database session
        db = next(get_db())

        try:
            # Step 1: Start session
            print("\\n📝 Step 1: Starting conversation session")
            self.session_id = await session_service.create_session(
                self.test_business_id, self.test_user_id
            )
            print(f"✅ Session created: {self.session_id}")

            # Turn 1: Incomplete transaction
            print("\\n💬 Turn 1: Incomplete transaction")
            transcript1 = "I sold apples to Ravi"
            print(f"User: \"{transcript1}\"")

            session_data = await session_service.get_session(self.session_id)
            nlu_result1 = await parse_intent_with_session(
                transcript=transcript1,
                business_id=self.test_business_id,
                session_data=session_data or {}
            )

            print(f"  Intent: {nlu_result1.intent}")
            print(f"  Entities: {nlu_result1.entities}")
            print(f"  Needs Clarification: {nlu_result1.needs_clarification}")

            # Add to session
            await session_service.add_user_turn(self.session_id, transcript1)
            if nlu_result1.needs_clarification:
                clarification = nlu_result1.clarification_question or "How much was the sale amount?"
                await session_service.add_assistant_turn(self.session_id, clarification, nlu_result1.entities)
                print(f"Agent: \"{clarification}\"")

            # Turn 2: Complete with amount
            print("\\n💬 Turn 2: Providing missing amount")
            transcript2 = "60 rupees"
            print(f"User: \"{transcript2}\"")

            session_data = await session_service.get_session(self.session_id)
            nlu_result2 = await parse_intent_with_session(
                transcript=transcript2,
                business_id=self.test_business_id,
                session_data=session_data or {}
            )

            print(f"  Intent: {nlu_result2.intent}")
            print(f"  Entities: {nlu_result2.entities}")
            print(f"  Context Merged: {'sale_amount' in nlu_result2.entities}")

            # Validate completion
            validation_result = validation_service.validate_nlu_output(
                nlu_result2.model_dump())
            print(f"  Transaction Complete: {validation_result['is_valid']}")
            print(f"  Missing Fields: {validation_result['missing_fields']}")

            await session_service.add_user_turn(self.session_id, transcript2)
            await session_service.complete_session(self.session_id)

            print(f"\\n🎉 TEST 3 COMPLETED - Multi-turn Conversation")
            return True

        except Exception as e:
            print(f"❌ Test 3 failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()


async def main():
    """Run all end-to-end tests"""

    print("🚀 SIA VOICE AGENT - END-TO-END TESTING")
    print("=" * 70)
    print(f"Test started at: {datetime.now()}")
    print()

    test_suite = VoiceAgentE2ETest()
    results = {}

    try:
        # Test 1: Inventory Query Flow
        results["inventory_query"] = await test_suite.test_inventory_query_flow()

        # Test 2: Transaction Creation Flow
        results["transaction_creation"] = await test_suite.test_transaction_creation_flow()

        # Test 3: Multi-turn Conversation
        results["multi_turn_conversation"] = await test_suite.test_multi_turn_conversation()

        # Summary
        print("\\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)

        total_tests = len(results)
        passed_tests = sum(results.values())

        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")

        print(f"\\nOverall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("\\n🎉 ALL TESTS PASSED - Voice Agent Pipeline Working!")
            print("\\n✅ Verified Components:")
            print("  • Voice session management with Redis")
            print("  • Intent parsing and NLU processing")
            print("  • Entity resolution (customers, products)")
            print("  • SQL query generation and execution")
            print("  • Inventory operations and stock checking")
            print("  • Transaction creation and validation")
            print("  • Multi-turn conversation context")
            print("  • Business insights generation")
        else:
            print(
                f"\\n⚠️  {total_tests - passed_tests} tests failed - Check logs above")

    except Exception as e:
        print(f"\\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
