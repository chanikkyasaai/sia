"""
Analysis Planner for SIA Voice Agent

Converts voice intents and entities into structured analysis specifications
for financial forecasting, risk assessment, and business insights.
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from app.services.sql_generator import SQLGenerator

logger = logging.getLogger(__name__)


class AnalysisPlanner:
    """LLM-powered analysis planner that converts voice intents to structured specifications"""

    def __init__(self):
        # Maximum constraints for performance
        self.MAX_ROWS = 5000
        self.MAX_DAYS = 365

        # Initialize SQL generator
        self.sql_generator = SQLGenerator()

        # Available database schema for LLM context
        self.database_schema = {
            "transactions": {
                "columns": ["id", "business_id", "user_id", "customer_id", "product_id", "type", "amount", "quantity", "payment_method", "transaction_date", "notes", "created_at"],
                "types": ["SALE", "PURCHASE", "CREDIT_GIVEN", "CREDIT_RECEIVED"],
                "description": "All business transactions including sales, purchases, and credit movements"
            },
            "customers": {
                "columns": ["id", "business_id", "name", "phone", "address", "balance", "created_at"],
                "description": "Customer information with outstanding balances (positive = owes money to business)"
            },
            "products": {
                "columns": ["id", "business_id", "name", "price", "category", "description", "is_active", "created_at"],
                "description": "Product catalog with pricing and categorization"
            },
            "inventory_items": {
                "columns": ["id", "business_id", "product_id", "quantity", "reorder_level", "last_updated"],
                "description": "Current stock levels and reorder thresholds"
            },
            "expenses": {
                "columns": ["id", "business_id", "user_id", "amount", "category", "description", "expense_date", "created_at"],
                "categories": ["UTILITIES", "RENT", "SUPPLIES", "MARKETING", "TRANSPORT", "OTHER"],
                "description": "Business expenses categorized for analysis"
            },
            "daily_analytics": {
                "columns": ["id", "business_id", "date", "total_sales", "total_purchases", "total_expenses", "credit_given", "credit_received", "net_cash_flow", "transaction_count", "customer_count"],
                "description": "Pre-aggregated daily business metrics for performance"
            },
            "reminders": {
                "columns": ["id", "business_id", "customer_id", "amount", "reminder_date", "status", "notes", "created_at"],
                "description": "Payment reminders and follow-up tracking"
            }
        }

    async def create_analysis_spec(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create analysis specification using GPT-4 for intelligent planning

        Args:
            business_id: Business UUID
            intent: Parsed intent (ASK_FORECAST, ASK_COLLECTION_PRIORITY, etc.)
            entities: Extracted entities from voice input

        Returns:
            JSON analysis specification
        """
        # Parse time range from entities first
        time_range = self._parse_time_range(entities)

        try:
            # Use GPT-4 to generate analysis specification
            return await self._generate_llm_analysis_spec(
                business_id, intent, entities, time_range
            )

        except Exception as e:
            logger.error(f"Analysis planning error for {intent}: {str(e)}")
            # Fallback to rule-based planning if LLM fails
            return await self._create_fallback_spec(business_id, intent, entities, time_range, str(e))

    async def _generate_llm_analysis_spec(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any],
        time_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Use GPT-4 to generate intelligent analysis specification
        """
        from app.services.llm import llm_service

        # Create comprehensive prompt for GPT-4
        prompt = self._create_analysis_planning_prompt(
            business_id, intent, entities, time_range
        )

        try:
            # Call GPT-4 for analysis planning using the full LLM service
            system_prompt = "You are an expert financial analyst and data scientist specializing in small business analytics. You create precise, actionable analysis specifications for voice-driven business intelligence requests."

            llm_response = await llm_service.call_full_llm(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=1500
            )

            if llm_response is not None:
                # LLM service returns JSON directly on success
                analysis_spec = llm_response

                # Validate and enhance the specification
                validated_spec = self._validate_and_enhance_spec(
                    analysis_spec, time_range)

                # Generate SQL queries for the analysis specification
                sql_queries = await self.sql_generator.generate_sql_queries(
                    validated_spec, business_id
                )

                # Add SQL queries to the specification
                validated_spec["sql_queries"] = sql_queries

                logger.info(
                    f"Successfully generated LLM analysis spec with {len(sql_queries)} SQL queries for {intent}")
                return validated_spec
            else:
                logger.error(
                    "LLM call returned None - likely parsing or API error")
                return await self._create_fallback_spec(business_id, intent, entities, time_range, "LLM call returned None")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            return await self._create_fallback_spec(business_id, intent, entities, time_range, "JSON parsing failed")
        except Exception as e:
            logger.error(f"LLM analysis planning failed: {str(e)}")
            return await self._create_fallback_spec(business_id, intent, entities, time_range, str(e))

    def _create_analysis_planning_prompt(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any],
        time_range: Dict[str, str]
    ) -> str:
        """
        Create comprehensive prompt for GPT-4 analysis planning
        """

        # Convert entities to readable format
        entities_text = "\n".join(
            [f"  - {k}: {v}" for k, v in entities.items()]) if entities else "  None specified"

        # Create database schema context
        schema_text = "\n".join([
            f"  {table}:\n    - Columns: {', '.join(info['columns'])}\n    - Description: {info['description']}"
            for table, info in self.database_schema.items()
        ])

        prompt = f"""
You are an analysis planner for SIA (voice-first financial assistant). Create a precise JSON analysis specification for the following business intelligence request.

BUSINESS CONTEXT:
- Business ID: {business_id}
- Request Intent: {intent}
- Extracted Entities:
{entities_text}
- Time Range: {time_range['start']} to {time_range['end']}

AVAILABLE DATABASE SCHEMA:
{schema_text}

CONSTRAINTS:
- Max rows: {self.MAX_ROWS}
- Max days: {self.MAX_DAYS}
- Performance optimized queries required

TASK:
Analyze the business request and create a structured analysis specification that:
1. Defines clear, measurable objectives
2. Specifies relevant business metrics to calculate
3. Determines appropriate data granularity (daily/weekly/monthly/per_customer)
4. Identifies exact database tables and columns needed
5. Determines if forecasting is required and the horizon
6. Provides implementation notes for data engineers

RESPONSE FORMAT:
Return ONLY valid JSON in this exact schema:

{{
  "analysis_spec": {{
    "objective": "clear 1-line business objective",
    "metrics": ["metric1", "metric2", "metric3"],
    "granularity": "daily|weekly|monthly|per_customer|per_product",
    "time_range": {{"start": "{time_range['start']}", "end": "{time_range['end']}"}},
    "forecast_needed": true|false,
    "forecast_horizon_days": number|null,
    "required_tables_columns": {{
      "table_name": ["col1", "col2"],
      "another_table": ["col3", "col4"]
    }},
    "notes": "specific implementation guidance for data processing"
  }}
}}

EXAMPLE ANALYSIS TYPES:
- Cashflow forecasting: Predict future cash position using historical patterns
- Collection priority: Rank customers by payment risk and outstanding amounts  
- Inventory burn-rate: Predict stock-out dates based on consumption patterns
- Sales trends: Identify patterns, seasonality, and growth opportunities
- Credit risk: Assess default probability using payment history
- Customer insights: Segment customers and calculate lifetime value
- Expense optimization: Identify cost reduction opportunities

Focus on:
- Business impact and actionability
- Data efficiency and performance
- Clear metrics that drive decisions
- Realistic forecasting horizons
- Specific implementation guidance

Generate the analysis specification now:"""

        return prompt

    def _validate_and_enhance_spec(
        self,
        analysis_spec: Dict[str, Any],
        time_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Validate and enhance LLM-generated analysis specification
        """
        spec = analysis_spec.get("analysis_spec", analysis_spec)

        # Ensure required fields exist with defaults
        validated_spec = {
            "analysis_spec": {
                "objective": spec.get("objective", "Business analysis objective"),
                "metrics": spec.get("metrics", ["total_sales", "transaction_count"]),
                "granularity": spec.get("granularity", "daily"),
                "time_range": spec.get("time_range", time_range),
                "forecast_needed": spec.get("forecast_needed", False),
                "forecast_horizon_days": spec.get("forecast_horizon_days"),
                "required_tables_columns": spec.get("required_tables_columns", {}),
                "notes": spec.get("notes", "LLM-generated analysis specification")
            }
        }

        # Validate and constrain forecast horizon
        if validated_spec["analysis_spec"]["forecast_needed"]:
            horizon = validated_spec["analysis_spec"]["forecast_horizon_days"]
            if horizon is None:
                # Default
                validated_spec["analysis_spec"]["forecast_horizon_days"] = 7
            elif horizon > 90:  # Cap at 90 days for performance
                validated_spec["analysis_spec"]["forecast_horizon_days"] = 90

        # Validate granularity options
        valid_granularities = ["daily", "weekly",
                               "monthly", "per_customer", "per_product"]
        if validated_spec["analysis_spec"]["granularity"] not in valid_granularities:
            validated_spec["analysis_spec"]["granularity"] = "daily"

        # Ensure metrics is a list
        if not isinstance(validated_spec["analysis_spec"]["metrics"], list):
            validated_spec["analysis_spec"]["metrics"] = ["total_sales"]

        # Validate table names against known schema
        validated_tables = {}
        for table, columns in validated_spec["analysis_spec"]["required_tables_columns"].items():
            if table in self.database_schema:
                # Filter columns to only those that exist in schema
                valid_columns = [
                    col for col in columns
                    if col in self.database_schema[table]["columns"]
                ]
                if valid_columns:
                    validated_tables[table] = valid_columns

        validated_spec["analysis_spec"]["required_tables_columns"] = validated_tables

        return validated_spec

    async def _create_fallback_spec(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any],
        time_range: Dict[str, str],
        error_msg: str
    ) -> Dict[str, Any]:
        """
        Create fallback analysis specification when LLM fails
        """
        fallback_spec = {
            "analysis_type": "general_analytics",
            "objective": f"Fallback analysis for {intent} - {error_msg}",
            "metrics": ["total_revenue", "total_expenses", "transaction_count"],
            "dimensions": ["date"],
            "time_range": time_range,
            "filters": {},
            "forecast_needed": "forecast" in intent.lower(),
            "forecast_horizon_days": 7 if "forecast" in intent.lower() else None,
            "notes": f"Fallback specification due to: {error_msg}"
        }

        # Generate SQL queries for fallback spec
        try:
            sql_queries = await self.sql_generator.generate_sql_queries(fallback_spec, business_id)
            fallback_spec["sql_queries"] = sql_queries
        except Exception as e:
            logger.error(f"Failed to generate SQL for fallback spec: {str(e)}")
            fallback_spec["sql_queries"] = []

        return fallback_spec

    def _parse_time_range(self, entities: Dict[str, Any]) -> Dict[str, str]:
        """Parse time range from entities"""

        date_range = entities.get("date_range", "last_30_days")
        end_date = date.today()

        # Parse common date range patterns
        if date_range == "last_7_days" or date_range == "week":
            start_date = end_date - timedelta(days=7)
        elif date_range == "last_30_days" or date_range == "month":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last_90_days" or date_range == "quarter":
            start_date = end_date - timedelta(days=90)
        elif date_range == "last_180_days" or date_range == "6months":
            start_date = end_date - timedelta(days=180)
        elif date_range == "last_365_days" or date_range == "year":
            start_date = end_date - timedelta(days=365)
        elif date_range == "today":
            start_date = end_date
        elif date_range == "yesterday":
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        else:
            # Default to last 30 days
            start_date = end_date - timedelta(days=30)

        # Enforce maximum days constraint
        if (end_date - start_date).days > self.MAX_DAYS:
            start_date = end_date - timedelta(days=self.MAX_DAYS)

        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }


# Singleton instance
analysis_planner = AnalysisPlanner()
