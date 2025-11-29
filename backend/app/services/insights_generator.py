"""
Insights Generator Service for SIA Analytics

Generates business insights from SQL query results using LLM analysis.
Produces structured insights in Hinglish+English mix for voice-first experience.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    LLM-powered insights generator that analyzes query results and produces
    actionable business insights in structured JSON format.
    """

    def __init__(self):
        self.llm_service = LLMService()

        # Business context categories for insight generation
        self.insight_categories = {
            "revenue_analysis": ["sales_trends", "revenue_growth", "transaction_patterns"],
            "customer_insights": ["customer_behavior", "retention", "segmentation"],
            "inventory_management": ["stock_levels", "turnover", "reorder_points"],
            "expense_analysis": ["cost_breakdown", "spending_patterns", "optimization"],
            "forecasting": ["trend_prediction", "seasonal_patterns", "growth_projection"],
            "risk_assessment": ["cash_flow", "credit_risk", "operational_risks"]
        }

    async def generate_insights(
        self,
        analysis_spec: Dict[str, Any],
        query_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate business insights from SQL query results.

        Args:
            analysis_spec: Original analysis specification
            query_results: Results from executed SQL queries (max 500 rows per query)

        Returns:
            Structured insights with summary, cards, risks, and actions
        """
        # Validate and process query results
        processed_results = self._process_query_results(query_results)

        if not processed_results:
            return self._create_no_data_insights(analysis_spec)

        try:
            # Create system prompt for insights generation
            system_prompt = self._create_insights_system_prompt()

            # Create user prompt with data and context
            user_prompt = self._create_insights_generation_prompt(
                analysis_spec, processed_results
            )

            # Call LLM for insights generation
            llm_response = await self.llm_service.call_full_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500
            )

            if llm_response is not None:
                # Validate and return insights
                validated_insights = self._validate_insights_response(
                    llm_response)
                logger.info(
                    f"Generated insights for {analysis_spec.get('analysis_type', 'unknown')} analysis")
                return validated_insights
            else:
                logger.error("LLM insights generation failed - returned None")
                return self._create_fallback_insights(analysis_spec, processed_results)

        except Exception as e:
            logger.error(f"Insights generation failed: {str(e)}")
            return self._create_fallback_insights(analysis_spec, processed_results)

    def _create_insights_system_prompt(self) -> str:
        """Create system prompt for insights generation role."""
        return """You are a business analyst for SIA (voice-first financial assistant). Your role is to:

1. Analyze SQL query results and provide a concise summary
2. Use natural Hinglish+English mix for Indian business communication
3. Focus ONLY on what was analyzed and key findings
4. Use ONLY the provided data - never hallucinate numbers
5. Output strict JSON format: {"summary_text": "...", "query_summary": "..."}

STRICT RULES:
- Use ONLY numbers and data from provided query results
- Mix Hinglish naturally: "Data analysis complete hai" or "Query successful raha"
- Keep summary concise (max 200 chars)
- Mention what queries were executed and key results
- Focus on data overview, not detailed insights
- Output ONLY valid JSON, no markdown or explanations

OUTPUT STRUCTURE:
{
  "summary_text": "Brief analysis summary with key numbers in Hinglish",
  "query_summary": "What queries were executed and their results"
}"""

    def _create_insights_generation_prompt(
        self,
        analysis_spec: Dict[str, Any],
        query_results: List[Dict[str, Any]]
    ) -> str:
        """Create detailed prompt for insights generation."""

        # Extract analysis context
        analysis_type = analysis_spec.get("analysis_type", "general")
        objective = analysis_spec.get("objective", "Business analysis")
        metrics = analysis_spec.get("metrics", [])
        time_range = analysis_spec.get("time_range", {})

        # Format query results for analysis
        results_summary = self._format_results_for_prompt(query_results)

        prompt = f"""Generate a concise analysis summary for this business query:

ANALYSIS CONTEXT:
- Type: {analysis_type}
- Objective: {objective}
- Metrics: {', '.join(metrics) if metrics else 'General metrics'}
- Time Range: {time_range.get('start', 'N/A')} to {time_range.get('end', 'N/A')}

QUERY RESULTS DATA:
{results_summary}

REQUIREMENTS:
1. Provide a brief summary of what was analyzed with key numbers
2. Describe what queries were executed and their main results
3. Use natural Hinglish+English mix
4. Keep summary concise and factual (max 200 chars each)
5. Use ₹ symbol for Indian rupees
6. Focus on data overview, not detailed insights

Output format:
{{
  "summary_text": "Brief analysis overview in Hinglish with key numbers (max 200 chars)",
  "query_summary": "Description of queries executed and main results (max 200 chars)"
}}"""

        return prompt

    def _process_query_results(self, query_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate query results for insights generation."""
        processed = []

        for result in query_results:
            if not result.get("success", False):
                continue

            data = result.get("data", [])
            if not data:
                continue

            # Limit data to prevent overwhelming LLM
            limited_data = data[:500] if len(data) > 500 else data

            processed.append({
                "description": result.get("description", "Query result"),
                "row_count": len(limited_data),
                "data": limited_data,
                "query_index": result.get("query_index", 0)
            })

        return processed

    def _format_results_for_prompt(self, processed_results: List[Dict[str, Any]]) -> str:
        """Format query results for LLM prompt."""
        if not processed_results:
            return "No data available for analysis"

        formatted_lines = []

        for result in processed_results:
            description = result["description"]
            row_count = result["row_count"]
            data = result["data"]

            formatted_lines.append(
                f"\nQuery: {description} ({row_count} rows)")

            # Sample first few rows for analysis
            sample_data = data[:10] if len(data) > 10 else data

            if sample_data:
                # Format as simple key-value pairs
                for i, row in enumerate(sample_data):
                    row_items = [f"{k}={v}" for k,
                                 v in row.items() if v is not None]
                    formatted_lines.append(
                        f"  Row {i+1}: {', '.join(row_items)}")

                if len(data) > 10:
                    formatted_lines.append(
                        f"  ... and {len(data) - 10} more rows")

        return "\n".join(formatted_lines)

    def _validate_insights_response(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process LLM insights response."""
        try:
            # Ensure required fields exist
            required_fields = ["summary_text", "query_summary"]

            for field in required_fields:
                if field not in llm_response:
                    logger.warning(
                        f"LLM response missing required field: {field}")
                    llm_response[field] = "Analysis completed" if field == "summary_text" else "Query executed successfully"

            return {
                # Limit length to 200 chars each
                "summary_text": str(llm_response.get("summary_text", ""))[:200],
                "query_summary": str(llm_response.get("query_summary", ""))[:200]
            }

        except Exception as e:
            logger.error(f"Insights response validation failed: {str(e)}")
            return self._create_error_insights(str(e))

    def _create_fallback_insights(
        self,
        analysis_spec: Dict[str, Any],
        processed_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create basic fallback insights when LLM fails."""

        total_rows = sum(result["row_count"] for result in processed_results)
        analysis_type = analysis_spec.get("analysis_type", "general")

        return {
            "summary_text": f"Analysis complete: {total_rows} records processed kar liye for {analysis_type}",
            "query_summary": f"{len(processed_results)} queries successfully execute huye with {total_rows} total rows"
        }

    def _create_no_data_insights(self, analysis_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create insights when no data is available."""
        return {
            "summary_text": "Koi data nahi mila analysis ke liye. Database check karo.",
            "query_summary": "Queries execute huye but no data found. Data entry start karo."
        }

    def _create_error_insights(self, error_message: str) -> Dict[str, Any]:
        """Create insights for error scenarios."""
        return {
            "summary_text": "Analysis mein technical issue aaya hai. Try again karo.",
            "query_summary": f"Query execution failed: {error_message[:100]}..."
        }
