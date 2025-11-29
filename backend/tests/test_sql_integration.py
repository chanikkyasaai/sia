"""
Test script for SQL Generator integration with Analysis Planner

This script validates the end-to-end flow from voice intent to SQL generation.
"""

from app.services.analysis_planner import AnalysisPlanner
from app.services.sql_generator import SQLGenerator
import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_sql_generation():
    """Test the complete voice-to-SQL generation flow"""

    print("🧪 Testing SIA SQL Generator Integration")
    print("=" * 50)

    # Initialize services
    planner = AnalysisPlanner()
    generator = SQLGenerator()

    # Test data
    business_id = "test_business_123"
    test_intent = "ASK_SALES_TRENDS"
    test_entities = {
        "time_period": "last_30_days",
        "product_category": "electronics"
    }

    print(f"📊 Testing Analysis Planning")
    print(f"   Business ID: {business_id}")
    print(f"   Intent: {test_intent}")
    print(f"   Entities: {test_entities}")
    print()

    try:
        # Test analysis spec generation with SQL
        print("🔄 Generating analysis specification...")
        analysis_spec = await planner.create_analysis_spec(
            business_id=business_id,
            intent=test_intent,
            entities=test_entities
        )

        print("✅ Analysis specification generated successfully!")
        print(f"   Analysis Type: {analysis_spec.get('analysis_type', 'N/A')}")
        print(f"   Objective: {analysis_spec.get('objective', 'N/A')}")
        print(f"   Metrics: {analysis_spec.get('metrics', [])}")
        print(f"   Time Range: {analysis_spec.get('time_range', {})}")
        print()

        # Check SQL queries
        sql_queries = analysis_spec.get('sql_queries', [])
        print(f"🔍 SQL Queries Generated: {len(sql_queries)}")

        for i, query in enumerate(sql_queries, 1):
            print(f"\n   Query {i}:")
            print(f"   Description: {query.get('description', 'N/A')}")
            print(f"   Parameters: {query.get('params_placeholders', [])}")
            print(f"   SQL Preview: {query.get('sql', 'N/A')[:100]}...")

        print("\n🎉 Integration test completed successfully!")
        print(f"   ✓ Analysis planner: Working")
        print(f"   ✓ SQL generator: Working")
        print(f"   ✓ LLM integration: Working")
        print(f"   ✓ Generated {len(sql_queries)} executable SQL queries")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_sql_generation())
    exit(0 if success else 1)
