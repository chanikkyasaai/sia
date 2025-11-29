"""
Unified Analysis Service for SIA Voice Agent

Combines analysis planning and SQL generation into a single LLM call for efficiency.
Generates both analysis specifications and executable SQL queries in one step.
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from app.services.llm import LLMService
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class UnifiedAnalyzer:
    """
    Unified analysis service that combines analysis planning and SQL generation
    into a single, efficient LLM call for better performance and consistency.
    """

    def __init__(self):
        self.llm_service = LLMService()

        # Performance constraints
        self.MAX_ROWS = 5000
        self.MAX_DAYS = 365
        self.MAX_QUERIES = 5

        # SQL execution constraints
        self.MAX_ROWS_PER_QUERY = 500
        self.MAX_TOTAL_ROWS = 2000
        # Complete database schema for comprehensive analysis
        self.QUERY_TIMEOUT_SECONDS = 30
        self.database_schema = {
            "transactions": {
                "columns": ["id", "business_id", "customer_id", "product_id", "type", "amount", "quantity", "note", "source", "created_at"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "customer_id": "INTEGER",
                    "product_id": "INTEGER", "type": "VARCHAR", "amount": "DECIMAL",
                    "quantity": "DECIMAL", "note": "TEXT", "source": "VARCHAR", "created_at": "TIMESTAMP"
                },
                "enums": {"type": ["SALE", "PURCHASE", "CREDIT_GIVEN", "CREDIT_RECEIVED"]},
                "description": "All business transactions including sales, purchases, and credit movements"
            },
            "customers": {
                "columns": ["id", "business_id", "name", "phone", "address", "balance", "created_at"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "name": "VARCHAR",
                    "phone": "VARCHAR", "address": "TEXT", "balance": "DECIMAL", "created_at": "TIMESTAMP"
                },
                "description": "Customer information with outstanding balances (positive = customer owes money to business)"
            },
            "products": {
                "columns": ["id", "business_id", "name", "price", "category", "description", "low_stock_threshold", "is_active", "created_at"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "name": "VARCHAR", "price": "DECIMAL",
                    "category": "VARCHAR", "description": "TEXT", "low_stock_threshold": "INTEGER",
                    "is_active": "BOOLEAN", "created_at": "TIMESTAMP"
                },
                "description": "Product catalog with pricing, categorization and stock thresholds"
            },
            "inventory_items": {
                "columns": ["id", "business_id", "product_id", "quantity_on_hand", "reorder_level", "updated_at"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "product_id": "INTEGER",
                    "quantity_on_hand": "DECIMAL", "reorder_level": "INTEGER", "updated_at": "TIMESTAMP"
                },
                "description": "Current stock levels and inventory management"
            },
            "expenses": {
                "columns": ["id", "business_id", "user_id", "amount", "category", "description", "expense_date", "created_at"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "user_id": "INTEGER", "amount": "DECIMAL",
                    "category": "VARCHAR", "description": "TEXT", "expense_date": "TIMESTAMP", "created_at": "TIMESTAMP"
                },
                "enums": {"category": ["UTILITIES", "RENT", "SUPPLIES", "MARKETING", "TRANSPORT", "OTHER"]},
                "description": "Business expenses categorized for cost analysis"
            },
            "daily_analytics": {
                "columns": ["id", "business_id", "date", "total_sales", "total_purchases", "total_expenses", "transaction_count", "customer_count"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "date": "DATE", "total_sales": "DECIMAL",
                    "total_purchases": "DECIMAL", "total_expenses": "DECIMAL", "transaction_count": "INTEGER", "customer_count": "INTEGER"
                },
                "description": "Pre-aggregated daily business metrics for performance optimization"
            },
            "reminders": {
                "columns": ["id", "business_id", "customer_id", "amount", "reminder_date", "status", "notes", "created_at"],
                "types": {
                    "id": "INTEGER", "business_id": "INTEGER", "customer_id": "INTEGER", "amount": "DECIMAL",
                    "reminder_date": "TIMESTAMP", "status": "VARCHAR", "notes": "TEXT", "created_at": "TIMESTAMP"
                },
                "description": "Payment reminders and follow-up tracking"
            }
        }

    async def create_unified_analysis(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create complete analysis specification with SQL queries in a single LLM call.

        Args:
            business_id: Business identifier
            intent: Voice intent (ASK_FORECAST, ASK_COLLECTION_PRIORITY, etc.)
            entities: Extracted entities from voice input

        Returns:
            Unified analysis specification with executable SQL queries
        """
        time_range = self._parse_time_range(entities)

        try:
            # Single LLM call for both analysis planning and SQL generation
            unified_spec = await self._generate_unified_spec(
                business_id, intent, entities, time_range
            )

            # Validate and enhance the specification
            validated_spec = self._validate_unified_spec(
                unified_spec, time_range)

            logger.info(
                f"Successfully generated unified analysis with {len(validated_spec.get('sql_queries', []))} SQL queries for {intent}"
            )
            return validated_spec

        except Exception as e:
            logger.error(f"Unified analysis failed for {intent}: {str(e)}")
            return await self._create_fallback_analysis(business_id, intent, entities, time_range, str(e))

    async def create_complete_analysis(
        self,
        db: Session,
        business_id: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create unified analysis specification AND execute SQL queries in a single call.

        Args:
            db: Database session
            business_id: Business identifier
            intent: Voice intent
            entities: Extracted entities from voice input

        Returns:
            Complete analysis with specification, executed query results, and execution summary
        """
        time_range = self._parse_time_range(entities)

        try:
            # Step 1: Generate unified analysis specification
            unified_spec = await self._generate_unified_spec(
                business_id, intent, entities, time_range
            )

            # Validate and enhance the specification
            validated_spec = self._validate_unified_spec(
                unified_spec, time_range)

            # Step 2: Execute SQL queries immediately
            sql_queries = validated_spec.get('sql_queries', [])
            if sql_queries:
                query_results = await self._execute_sql_queries(
                    db=db,
                    sql_queries=sql_queries,
                    business_id=business_id,
                    time_range=time_range
                )

                execution_summary = self._get_execution_summary(query_results)

                # Add execution results to the validated spec
                validated_spec['query_results'] = query_results
                validated_spec['execution_summary'] = execution_summary
                validated_spec['execution_complete'] = True
            else:
                validated_spec['query_results'] = []
                validated_spec['execution_summary'] = {
                    "total_queries": 0,
                    "successful_queries": 0,
                    "failed_queries": 0,
                    "total_rows": 0,
                    "has_errors": False,
                    "execution_complete": True
                }
                validated_spec['execution_complete'] = False

            logger.info(
                f"Successfully completed unified analysis and execution for {intent}: "
                f"{len(sql_queries)} queries, {validated_spec['execution_summary']['total_rows']} rows"
            )
            return validated_spec

        except Exception as e:
            logger.error(
                f"Complete unified analysis failed for {intent}: {str(e)}")
            fallback = await self._create_fallback_analysis(business_id, intent, entities, time_range, str(e))
            fallback['execution_complete'] = False
            fallback['execution_error'] = str(e)
            return fallback

    async def _generate_unified_spec(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any],
        time_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate unified analysis specification with SQL queries in single LLM call."""

        system_prompt = self._create_system_prompt()
        user_prompt = self._create_unified_prompt(
            business_id, intent, entities, time_range)

        llm_response = await self.llm_service.call_full_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000  # Increased for combined response
        )

        if llm_response is not None:
            return llm_response
        else:
            raise Exception("LLM call returned None - API or parsing error")

    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt for unified analysis."""
        return """You are a senior business intelligence analyst and SQL expert for SIA (voice-first financial assistant). 

Your role is to:
1. Analyze voice-driven business intelligence requests
2. Create structured analysis specifications 
3. Generate efficient, parameterized SQL queries
4. Ensure business impact and actionability

CORE PRINCIPLES:
- Focus on actionable business insights that drive decisions
- Generate ONLY SELECT/aggregation queries (no DDL/DML)
- Use parameterized queries with $1, $2, $3... placeholders
- All queries MUST filter by business_id = $1 (first parameter)
- Optimize for performance with appropriate limits and indexes
- Consider business context and realistic forecasting horizons

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON in the specified schema
- Maximum 5 SQL queries per analysis
- Each query must have clear business purpose
- Include meaningful JOINs for comprehensive analysis
- Add appropriate GROUP BY and ORDER BY clauses
- Parameter placeholders must be sequential: $1, $2, $3...

RESPONSE SCHEMA:
{
  "analysis_spec": {
    "objective": "clear business objective (1 line)",
    "analysis_type": "forecast|risk_assessment|trend_analysis|performance|optimization",
    "metrics": ["list", "of", "business", "metrics"],
    "granularity": "daily|weekly|monthly|per_customer|per_product",
    "time_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "forecast_needed": true|false,
    "forecast_horizon_days": number|null,
    "business_impact": "expected business value/decisions enabled",
    "notes": "implementation guidance"
  },
  "sql_queries": [
    {
      "sql": "SELECT ... FROM ... WHERE business_id = $1 AND ...",
      "params_placeholders": ["business_id", "start_date", "end_date"],
      "description": "business purpose of this query",
      "expected_rows": "estimated row count",
      "business_value": "what insight this query provides"
    }
  ]
}

STRICT RULES:
- NO INSERT, UPDATE, DELETE, CREATE, DROP statements
- ALL queries must include WHERE business_id = $1
- Use proper SQL aggregations (SUM, AVG, COUNT, MAX, MIN)
- Keep queries focused and efficient
- Validate all table and column names against provided schema"""

    def _create_unified_prompt(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any],
        time_range: Dict[str, str]
    ) -> str:
        """Create comprehensive prompt for unified analysis and SQL generation."""

        # Format entities for readability
        entities_text = "\n".join([
            f"  - {k}: {v}" for k, v in entities.items()
        ]) if entities else "  None specified"

        # Create detailed schema documentation
        schema_text = self._format_schema_documentation()

        # Intent-specific guidance
        intent_guidance = self._get_intent_specific_guidance(intent)

        prompt = f"""
BUSINESS INTELLIGENCE REQUEST:
- Business ID: {business_id}
- Voice Intent: {intent}
- Extracted Entities:
{entities_text}
- Analysis Time Range: {time_range['start']} to {time_range['end']}

DATABASE SCHEMA:
{schema_text}

INTENT-SPECIFIC GUIDANCE:
{intent_guidance}

CONSTRAINTS:
- Maximum {self.MAX_QUERIES} SQL queries
- Maximum {self.MAX_ROWS} rows per query
- Maximum {self.MAX_DAYS} days analysis window
- Query timeout: 30 seconds
- Performance optimized queries required

TASK:
Create a comprehensive business intelligence analysis that:

1. ANALYSIS SPECIFICATION:
   - Define clear, measurable business objective
   - Identify key metrics that drive business decisions
   - Determine appropriate data granularity for insights
   - Assess if forecasting is needed and realistic horizon
   - Explain expected business impact and value

2. SQL QUERY GENERATION:
   - Generate 1-{self.MAX_QUERIES} efficient SELECT queries
   - Use parameterized queries with $1=business_id, $2=start_date, $3=end_date
   - Include meaningful JOINs for comprehensive analysis
   - Add proper aggregations, grouping, and ordering
   - Validate all table/column names against schema
   - Optimize for performance and business insights

EXAMPLE ANALYSIS PATTERNS:
- Cashflow Forecasting: Historical patterns → Future cash position prediction
- Collection Priority: Payment history + outstanding amounts → Risk ranking
- Inventory Optimization: Consumption patterns → Stock-out predictions  
- Sales Intelligence: Transaction trends → Growth opportunities identification
- Customer Insights: Behavior patterns → Segmentation and lifetime value
- Credit Risk Assessment: Payment history → Default probability scoring
- Expense Analysis: Cost patterns → Optimization opportunities

Focus on:
✓ Actionable insights that enable business decisions
✓ Data-driven recommendations with clear next steps
✓ Performance-optimized queries with business context
✓ Realistic forecasting based on available data
✓ Clear business value proposition for each query

Generate the unified analysis specification with SQL queries now:
"""

        return prompt

    def _format_schema_documentation(self) -> str:
        """Format database schema with types and relationships."""
        schema_lines = []

        for table_name, table_info in self.database_schema.items():
            # Create column definitions with types
            columns_with_types = []
            for col in table_info['columns']:
                col_type = table_info['types'].get(col, 'UNKNOWN')
                columns_with_types.append(f"{col} ({col_type})")

            # Add enum values if available
            enum_info = ""
            if 'enums' in table_info:
                enum_details = []
                for field, values in table_info['enums'].items():
                    enum_details.append(f"{field}: {', '.join(values)}")
                if enum_details:
                    enum_info = f"\n    Enums: {'; '.join(enum_details)}"

            schema_lines.append(
                f"  {table_name}:\n"
                f"    Columns: {', '.join(columns_with_types)}{enum_info}\n"
                f"    Purpose: {table_info['description']}"
            )

        return "\n\n".join(schema_lines)

    def _get_intent_specific_guidance(self, intent: str) -> str:
        """Provide intent-specific analysis guidance."""

        guidance_map = {
            "ASK_FORECAST": """
CASHFLOW FORECASTING:
- Analyze historical daily/weekly cash flows from transactions
- Identify seasonal patterns and trends
- Project future cash position based on patterns
- Include both revenue (sales) and expenses
- Flag potential cash flow gaps or surpluses
- Recommend optimal cash management actions""",

            "ASK_COLLECTION_PRIORITY": """
COLLECTION PRIORITY ANALYSIS:
- Rank customers by outstanding balance amount
- Analyze payment history and patterns
- Calculate days outstanding for each customer
- Assess payment risk based on historical behavior
- Prioritize collection efforts by potential recovery value
- Identify customers needing immediate attention""",

            "ASK_CASHFLOW_HEALTH": """
CASHFLOW HEALTH ASSESSMENT:
- Calculate net cash flow trends over time
- Analyze cash conversion cycle efficiency
- Compare inflows vs outflows by period
- Identify cash flow volatility and stability
- Assess working capital requirements
- Flag concerning patterns or improvements""",

            "ASK_INVENTORY_BURNRATE": """
INVENTORY BURN RATE ANALYSIS:
- Calculate consumption rates for each product
- Predict stock-out dates based on current levels
- Identify fast-moving vs slow-moving inventory
- Analyze reorder patterns and optimization
- Flag products needing immediate restocking
- Recommend inventory optimization strategies""",

            "ASK_CUSTOMER_INSIGHTS": """
CUSTOMER INTELLIGENCE ANALYSIS:
- Segment customers by purchase behavior
- Calculate customer lifetime value (CLV)
- Analyze purchase frequency and patterns
- Identify high-value and at-risk customers
- Track customer acquisition and retention
- Recommend customer engagement strategies""",

            "ASK_SALES_TRENDS": """
SALES TREND ANALYSIS:
- Analyze sales performance over time periods
- Identify seasonal patterns and growth trends  
- Compare product performance and categories
- Calculate sales velocity and momentum
- Identify top-performing products/periods
- Recommend sales optimization strategies""",

            "ASK_EXPENSE_BREAKDOWN": """
EXPENSE ANALYSIS:
- Categorize and analyze expense patterns
- Identify cost optimization opportunities
- Track expense trends and anomalies
- Calculate expense ratios and efficiency metrics
- Compare periods for cost management insights
- Recommend expense reduction strategies""",

            "ASK_CREDIT_RISK": """
CREDIT RISK ASSESSMENT:
- Analyze customer payment history patterns
- Calculate payment delays and default rates
- Score customers by credit risk levels
- Identify high-risk customer segments
- Assess portfolio credit exposure
- Recommend credit management policies"""
        }

        return guidance_map.get(intent, "General business analysis focusing on key performance metrics and actionable insights.")

    def _validate_unified_spec(
        self,
        unified_spec: Dict[str, Any],
        time_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Validate and enhance unified analysis specification."""

        # Extract analysis spec
        analysis_spec = unified_spec.get("analysis_spec", {})
        sql_queries = unified_spec.get("sql_queries", [])

        # Validate analysis specification
        validated_analysis = {
            "objective": analysis_spec.get("objective", "Business intelligence analysis"),
            "analysis_type": analysis_spec.get("analysis_type", "performance"),
            "metrics": analysis_spec.get("metrics", ["total_sales", "transaction_count"]),
            "granularity": analysis_spec.get("granularity", "daily"),
            "time_range": analysis_spec.get("time_range", time_range),
            "forecast_needed": analysis_spec.get("forecast_needed", False),
            "forecast_horizon_days": analysis_spec.get("forecast_horizon_days"),
            "business_impact": analysis_spec.get("business_impact", "Improved business decision making"),
            "notes": analysis_spec.get("notes", "LLM-generated unified analysis")
        }

        # Validate forecast horizon
        if validated_analysis["forecast_needed"]:
            horizon = validated_analysis["forecast_horizon_days"]
            if horizon is None:
                validated_analysis["forecast_horizon_days"] = 7
            elif horizon > 90:
                validated_analysis["forecast_horizon_days"] = 90

        # Validate granularity
        valid_granularities = ["daily", "weekly",
                               "monthly", "per_customer", "per_product"]
        if validated_analysis["granularity"] not in valid_granularities:
            validated_analysis["granularity"] = "daily"

        # Validate SQL queries
        validated_queries = []
        # Limit number of queries
        for i, query in enumerate(sql_queries[:self.MAX_QUERIES]):
            if not isinstance(query, dict):
                continue

            sql = query.get("sql", "").strip()
            if not sql or not sql.upper().startswith("SELECT"):
                logger.warning(f"Invalid SQL query {i}: {sql[:50]}...")
                continue

            # Check for dangerous operations
            dangerous_keywords = ["INSERT", "UPDATE",
                                  "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
            if any(keyword in sql.upper() for keyword in dangerous_keywords):
                logger.warning(
                    f"Dangerous SQL operation in query {i}: {sql[:50]}...")
                continue

            # Ensure business_id filter exists
            if "business_id" not in sql.lower():
                logger.warning(
                    f"Query {i} missing business_id filter: {sql[:50]}...")
                continue

            validated_queries.append({
                "sql": sql,
                "params_placeholders": query.get("params_placeholders", ["business_id"]),
                "description": query.get("description", f"Query {i+1}"),
                "expected_rows": query.get("expected_rows", "< 1000"),
                "business_value": query.get("business_value", "Business insights")
            })

        return {
            "analysis_spec": validated_analysis,
            "sql_queries": validated_queries,
            "validation_summary": {
                "total_queries": len(validated_queries),
                "analysis_type": validated_analysis["analysis_type"],
                "forecast_enabled": validated_analysis["forecast_needed"],
                "time_span_days": (datetime.fromisoformat(time_range["end"]) -
                                   datetime.fromisoformat(time_range["start"])).days
            }
        }

    async def _create_fallback_analysis(
        self,
        business_id: str,
        intent: str,
        entities: Dict[str, Any],
        time_range: Dict[str, str],
        error_msg: str
    ) -> Dict[str, Any]:
        """Create fallback analysis when LLM fails."""

        # Basic fallback queries based on intent
        fallback_queries = []

        if "FORECAST" in intent or "CASHFLOW" in intent:
            fallback_queries.append({
                "sql": """
                    SELECT 
                        DATE(created_at) as date,
                        SUM(CASE WHEN type = 'SALE' THEN amount ELSE -amount END) as net_cashflow,
                        COUNT(*) as transaction_count
                    FROM transactions 
                    WHERE business_id = $1 
                        AND created_at >= $2 
                        AND created_at <= $3
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """,
                "params_placeholders": ["business_id", "start_date", "end_date"],
                "description": "Daily net cashflow analysis",
                "expected_rows": "< 100",
                "business_value": "Cash flow trend identification"
            })

        elif "CUSTOMER" in intent or "COLLECTION" in intent:
            fallback_queries.append({
                "sql": """
                    SELECT 
                        c.name,
                        c.balance as outstanding_amount,
                        COUNT(t.id) as transaction_count,
                        MAX(t.created_at) as last_transaction
                    FROM customers c
                    LEFT JOIN transactions t ON c.id = t.customer_id
                    WHERE c.business_id = $1 AND c.balance > 0
                    GROUP BY c.id, c.name, c.balance
                    ORDER BY c.balance DESC
                    LIMIT 50
                """,
                "params_placeholders": ["business_id"],
                "description": "Customer outstanding balance analysis",
                "expected_rows": "< 50",
                "business_value": "Collection priority identification"
            })

        else:
            # General sales analysis
            fallback_queries.append({
                "sql": """
                    SELECT 
                        DATE(created_at) as date,
                        SUM(CASE WHEN type = 'SALE' THEN amount ELSE 0 END) as total_sales,
                        COUNT(CASE WHEN type = 'SALE' THEN 1 END) as sale_count
                    FROM transactions 
                    WHERE business_id = $1 
                        AND created_at >= $2 
                        AND created_at <= $3
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """,
                "params_placeholders": ["business_id", "start_date", "end_date"],
                "description": "Daily sales performance analysis",
                "expected_rows": "< 100",
                "business_value": "Sales trend identification"
            })

        return {
            "analysis_spec": {
                "objective": f"Fallback analysis for {intent}",
                "analysis_type": "performance",
                "metrics": ["total_sales", "transaction_count"],
                "granularity": "daily",
                "time_range": time_range,
                "forecast_needed": False,
                "forecast_horizon_days": None,
                "business_impact": "Basic business metrics for decision support",
                "notes": f"Fallback analysis due to: {error_msg}"
            },
            "sql_queries": fallback_queries,
            "validation_summary": {
                "total_queries": len(fallback_queries),
                "analysis_type": "performance",
                "forecast_enabled": False,
                "fallback_used": True,
                "error_reason": error_msg
            }
        }

    def _parse_time_range(self, entities: Dict[str, Any]) -> Dict[str, str]:
        """Parse time range from entities with smart defaults."""

        date_range = entities.get("date_range", "last_30_days")
        end_date = date.today()

        # Parse common date range patterns
        range_mapping = {
            "last_7_days": 7, "week": 7, "last_week": 7,
            "last_30_days": 30, "month": 30, "last_month": 30,
            "last_90_days": 90, "quarter": 90, "last_quarter": 90,
            "last_180_days": 180, "6months": 180, "last_6_months": 180,
            "last_365_days": 365, "year": 365, "last_year": 365
        }

        if date_range == "today":
            start_date = end_date
        elif date_range == "yesterday":
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        else:
            days_back = range_mapping.get(date_range, 30)  # Default to 30 days
            start_date = end_date - timedelta(days=days_back)

        # Enforce maximum days constraint
        if (end_date - start_date).days > self.MAX_DAYS:
            start_date = end_date - timedelta(days=self.MAX_DAYS)

        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    async def _execute_sql_queries(
        self,
        db: Session,
        sql_queries: List[Dict[str, Any]],
        business_id: str,
        time_range: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL queries with proper parameterization and error handling.

        Args:
            db: Database session
            sql_queries: List of validated SQL query objects
            business_id: Business identifier for scoping
            time_range: Time range for parameter context

        Returns:
            List of query execution results with data, metadata, and error info
        """
        results = []
        total_rows_processed = 0

        logger.info(
            f"Executing {len(sql_queries)} SQL queries for business {business_id}")

        for i, query_obj in enumerate(sql_queries):
            # Skip if we've hit total row limit
            if total_rows_processed >= self.MAX_TOTAL_ROWS:
                logger.warning(
                    f"Hit total row limit ({self.MAX_TOTAL_ROWS}), skipping remaining queries")
                results.append(self._create_skipped_result(
                    i, query_obj, "Row limit exceeded"))
                continue

            result = await self._execute_single_query(
                db, query_obj, business_id, time_range, i
            )

            # Track total rows for limits
            if result.get("success", False):
                total_rows_processed += result.get("row_count", 0)

            results.append(result)

        logger.info(
            f"Query execution completed: {len(results)} queries, {total_rows_processed} total rows")
        return results

    async def _execute_single_query(
        self,
        db: Session,
        query_obj: Dict[str, Any],
        business_id: str,
        time_range: Dict[str, str],
        query_index: int
    ) -> Dict[str, Any]:
        """Execute a single SQL query with full error handling."""

        sql = ""
        description = f"Query {query_index + 1}"

        try:
            # Extract query components
            sql = query_obj.get("sql", "").strip()
            params_placeholders = query_obj.get("params_placeholders", [])
            description = query_obj.get(
                "description", f"Query {query_index + 1}")

            if not sql:
                return self._create_error_result(query_index, description, "Empty SQL query", sql)

            # Prepare parameters
            params_dict = self._prepare_query_parameters(
                business_id, params_placeholders, time_range)

            # Convert parameterized SQL ($1, $2) to named parameters (:param1, :param2)
            converted_sql, final_params = self._convert_sql_parameters(
                sql, params_placeholders, params_dict)

            logger.debug(
                f"Executing query {query_index}: {converted_sql[:100]}...")

            # Execute with timeout and row limit
            result = db.execute(text(converted_sql), final_params)

            # Ensure columns is always defined to avoid unbound variable issues
            columns = []

            # Fetch results with row limit
            rows = result.fetchmany(self.MAX_ROWS_PER_QUERY)

            # Convert to structured format
            if rows:
                columns = [col for col in result.keys()]
                data = [dict(zip(columns, row)) for row in rows]

                # Clean data (handle None values, format numbers)
                cleaned_data = self._clean_query_results(data)
            else:
                cleaned_data = []

            # Check if there are more rows (for warnings)
            remaining_rows = result.fetchone()
            has_more_data = remaining_rows is not None

            result_obj = {
                "query_index": query_index,
                "description": description,
                "success": True,
                "row_count": len(cleaned_data),
                "data": cleaned_data,
                "columns": columns,
                "sql": converted_sql,
                "parameters": final_params,
                "has_more_data": has_more_data,
                "execution_time_ms": None  # Could add timing if needed
            }

            if has_more_data:
                result_obj["warning"] = f"Results limited to {self.MAX_ROWS_PER_QUERY} rows"

            logger.info(
                f"Query {query_index} executed successfully: {len(cleaned_data)} rows")
            return result_obj

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query {query_index} execution failed: {error_msg}")
            return self._create_error_result(query_index, description, error_msg, sql)

    def _prepare_query_parameters(
        self,
        business_id: str,
        params_placeholders: List[str],
        time_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare parameter values for SQL execution."""

        params_dict: Dict[str, Any] = {"business_id": business_id}

        # Add time range parameters
        if "start_date" in params_placeholders and "start" in time_range:
            params_dict["start_date"] = time_range["start"]
        elif "start_date" in params_placeholders:
            # Default to 30 days ago if not specified
            default_start = (datetime.now() - timedelta(days=30)
                             ).strftime("%Y-%m-%d")
            params_dict["start_date"] = default_start

        if "end_date" in params_placeholders and "end" in time_range:
            params_dict["end_date"] = time_range["end"]
        elif "end_date" in params_placeholders:
            # Default to today if not specified
            params_dict["end_date"] = datetime.now().strftime("%Y-%m-%d")

        # Handle other common parameters with defaults
        for placeholder in params_placeholders:
            if placeholder not in params_dict:
                if placeholder == "limit":
                    params_dict[placeholder] = self.MAX_ROWS_PER_QUERY
                elif placeholder == "offset":
                    params_dict[placeholder] = 0
                else:
                    logger.warning(
                        f"No value provided for parameter: {placeholder}")

        return params_dict

    def _convert_sql_parameters(
        self,
        sql: str,
        params_placeholders: List[str],
        params_dict: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Convert $1, $2 style parameters to :param1, :param2 style for SQLAlchemy."""

        converted_sql = sql
        final_params = {}

        # Replace positional parameters ($1, $2) with named parameters (:param)
        for i, placeholder in enumerate(params_placeholders, 1):
            if placeholder in params_dict:
                placeholder_name = f"param_{placeholder}"
                converted_sql = converted_sql.replace(
                    f"${i}", f":{placeholder_name}")
                final_params[placeholder_name] = params_dict[placeholder]

        return converted_sql, final_params

    def _clean_query_results(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and format query results for insights generation."""

        cleaned_data = []

        for row in data:
            cleaned_row = {}

            for key, value in row.items():
                # Handle None values
                if value is None:
                    cleaned_row[key] = None
                # Format datetime objects
                elif hasattr(value, 'isoformat'):
                    cleaned_row[key] = value.isoformat()
                # Format decimal/float numbers
                elif isinstance(value, (float, int)):
                    # Round to reasonable precision for insights
                    if isinstance(value, float):
                        cleaned_row[key] = round(value, 2)
                    else:
                        cleaned_row[key] = value
                # Convert to string for other types
                else:
                    cleaned_row[key] = str(value)

            cleaned_data.append(cleaned_row)

        return cleaned_data

    def _create_error_result(
        self,
        query_index: int,
        description: str,
        error_msg: str,
        sql: str
    ) -> Dict[str, Any]:
        """Create standardized error result."""

        return {
            "query_index": query_index,
            "description": description,
            "success": False,
            "error": error_msg,
            "row_count": 0,
            "data": [],
            "columns": [],
            "sql": sql,
            "parameters": {},
            "has_more_data": False
        }

    def _create_skipped_result(
        self,
        query_index: int,
        query_obj: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Create result for skipped queries."""

        return {
            "query_index": query_index,
            "description": query_obj.get("description", f"Query {query_index + 1}"),
            "success": False,
            "error": f"Query skipped: {reason}",
            "row_count": 0,
            "data": [],
            "columns": [],
            "sql": query_obj.get("sql", ""),
            "parameters": {},
            "has_more_data": False,
            "skipped": True
        }

    def _get_execution_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate execution summary statistics."""

        total_queries = len(results)
        successful_queries = sum(1 for r in results if r.get("success", False))
        failed_queries = total_queries - successful_queries
        total_rows = sum(r.get("row_count", 0)
                         for r in results if r.get("success", False))

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "total_rows": total_rows,
            "has_errors": failed_queries > 0,
            "execution_complete": True
        }


# Singleton instance
unified_analyzer = UnifiedAnalyzer()
