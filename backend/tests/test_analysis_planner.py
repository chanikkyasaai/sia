"""
Test Analysis Planner - SIA Voice Agent

This file demonstrates the analysis planner functionality with sample requests.
"""

import asyncio
import json
from datetime import date, timedelta

# Sample test cases for analysis planning
ANALYSIS_TEST_CASES = [
    {
        "name": "7-Day Cashflow Forecast",
        "business_id": "123",
        "intent": "ASK_FORECAST",
        "entities": {
            "forecast_type": "cashflow",
            "forecast_period": "7_days",
            "date_range": "last_90_days"
        },
        "expected_metrics": ["daily_total_sales", "daily_total_expenses", "daily_net_cashflow"],
        "expected_forecast": True
    },
    {
        "name": "Collection Priority Analysis",
        "business_id": "123",
        "intent": "ASK_COLLECTION_PRIORITY",
        "entities": {
            "date_range": "last_30_days"
        },
        "expected_metrics": ["outstanding_balance", "days_overdue", "payment_history_score"],
        "expected_forecast": False
    },
    {
        "name": "Inventory Burn-Rate for Specific Product",
        "business_id": "123",
        "intent": "ASK_INVENTORY_BURNRATE",
        "entities": {
            "product_name": "apples",
            "date_range": "last_60_days"
        },
        "expected_metrics": ["burn_rate", "stock_level", "days_until_stockout"],
        "expected_forecast": True
    },
    {
        "name": "Sales Trends Analysis",
        "business_id": "123",
        "intent": "ASK_SALES_TRENDS",
        "entities": {
            "date_range": "last_90_days"
        },
        "expected_metrics": ["daily_sales", "product_performance", "sales_growth_rate"],
        "expected_forecast": False
    },
    {
        "name": "Credit Risk Assessment",
        "business_id": "123",
        "intent": "ASK_CREDIT_RISK",
        "entities": {
            "date_range": "last_180_days"
        },
        "expected_metrics": ["credit_score", "default_probability", "payment_delay_days"],
        "expected_forecast": True
    },
    {
        "name": "Customer Insights",
        "business_id": "123",
        "intent": "ASK_CUSTOMER_INSIGHTS",
        "entities": {
            "date_range": "last_365_days"
        },
        "expected_metrics": ["customer_lifetime_value", "purchase_frequency", "average_order_value"],
        "expected_forecast": False
    },
    {
        "name": "Expense Breakdown",
        "business_id": "123",
        "intent": "ASK_EXPENSE_BREAKDOWN",
        "entities": {
            "date_range": "last_90_days"
        },
        "expected_metrics": ["expense_by_category", "expense_trends", "expense_ratio"],
        "expected_forecast": False
    },
    {
        "name": "Monthly Sales Forecast",
        "business_id": "123",
        "intent": "ASK_FORECAST",
        "entities": {
            "forecast_type": "sales",
            "forecast_period": "30_days",
            "date_range": "last_90_days"
        },
        "expected_metrics": ["daily_total_sales", "transaction_count", "average_sale_value"],
        "expected_forecast": True
    }
]


async def test_analysis_planner():
    """Test the analysis planner with sample cases"""

    from app.services.analysis_planner import analysis_planner

    print("=== TESTING ANALYSIS PLANNER ===\\n")

    for i, test_case in enumerate(ANALYSIS_TEST_CASES, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * (len(test_case['name']) + 8))

        try:
            # Generate analysis specification
            result = analysis_planner.create_analysis_spec(
                business_id=test_case["business_id"],
                intent=test_case["intent"],
                entities=test_case["entities"]
            )

            spec = result["analysis_spec"]

            print(f"✅ Objective: {spec['objective']}")
            print(f"📊 Metrics: {', '.join(spec['metrics'])}")
            print(f"📅 Granularity: {spec['granularity']}")
            print(
                f"⏰ Time Range: {spec['time_range']['start']} to {spec['time_range']['end']}")
            print(f"🔮 Forecast Needed: {spec['forecast_needed']}")

            if spec['forecast_needed']:
                print(
                    f"📈 Forecast Horizon: {spec['forecast_horizon_days']} days")

            print(
                f"🗃️ Required Tables: {', '.join(spec['required_tables_columns'].keys())}")

            if spec['notes']:
                print(f"📝 Notes: {spec['notes']}")

            # Validation
            assert spec['forecast_needed'] == test_case['expected_forecast'], f"Forecast expectation mismatch"
            assert any(metric in spec['metrics']
                       for metric in test_case['expected_metrics']), f"Expected metrics not found"

            print("✅ Test passed\\n")

        except Exception as e:
            print(f"❌ Test failed: {str(e)}\\n")


def print_api_examples():
    """Print sample API calls for analysis planning"""

    print("=== API EXAMPLES ===\\n")

    examples = [
        {
            "title": "Voice Agent with Analysis Intent",
            "endpoint": "POST /voice/agent",
            "payload": {
                "business_id": 1,
                "user_id": 1,
                "transcript": "Show me 7-day cashflow forecast"
            }
        },
        {
            "title": "Direct Analysis Specification",
            "endpoint": "POST /voice/agent/analysis",
            "payload": {
                "business_id": 1,
                "intent": "ASK_FORECAST",
                "entities": {
                    "forecast_type": "cashflow",
                    "forecast_period": "7_days",
                    "date_range": "last_90_days"
                }
            }
        },
        {
            "title": "Collection Priority Analysis",
            "endpoint": "POST /voice/agent/analysis",
            "payload": {
                "business_id": 1,
                "intent": "ASK_COLLECTION_PRIORITY",
                "entities": {
                    "date_range": "last_30_days"
                }
            }
        },
        {
            "title": "Inventory Burn-Rate Analysis",
            "endpoint": "POST /voice/agent/analysis",
            "payload": {
                "business_id": 1,
                "intent": "ASK_INVENTORY_BURNRATE",
                "entities": {
                    "product_name": "apples",
                    "date_range": "last_60_days"
                }
            }
        }
    ]

    for example in examples:
        print(f"### {example['title']}")
        print(f"```bash")
        print(f"curl -X POST http://localhost:8000{example['endpoint']} \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f"  -d '{json.dumps(example['payload'], indent=2)}'")
        print("```\\n")


def print_sample_output():
    """Print sample analysis specification output"""

    print("=== SAMPLE ANALYSIS SPECIFICATION OUTPUT ===\\n")

    sample_output = {
        "analysis_spec": {
            "objective": "7-day cashflow forecast using last 90 days of daily net cash",
            "metrics": ["daily_total_sales", "daily_total_expenses", "daily_net_cashflow"],
            "granularity": "daily",
            "time_range": {
                "start": "2025-08-30",
                "end": "2025-11-29"
            },
            "forecast_needed": True,
            "forecast_horizon_days": 7,
            "required_tables_columns": {
                "transactions": ["transaction_date", "type", "amount"],
                "expenses": ["expense_date", "amount"],
                "daily_analytics": ["date", "total_sales", "total_expenses", "net_cash_flow"]
            },
            "notes": "Aggregate sales as SUM(amount) WHERE type IN ('SALE', 'CREDIT_RECEIVED'); expenses from expenses table"
        }
    }

    print("```json")
    print(json.dumps(sample_output, indent=2))
    print("```\\n")


async def main():
    """Run all tests and examples"""

    print("SIA ANALYSIS PLANNER - TESTING\\n")
    print("=" * 50)

    try:
        # Test analysis planner
        await test_analysis_planner()

        # Print API examples
        print_api_examples()

        # Print sample output
        print_sample_output()

        print("=== ALL TESTS COMPLETED ===")
        print("\\nNext Steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Test the analysis endpoints using the curl commands above")
        print("3. Integrate with data processing engine to execute analysis specs")

    except Exception as e:
        print(f"Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
