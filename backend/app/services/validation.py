"""
Validation service for NLU output and intent-based field validation
"""
import json
import logging
from typing import Dict, Any, List, Set
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# Intent → Required fields mapping
REQUIRED_FIELDS_BY_INTENT = {
    # Transaction intents
    "TXN_SALE": ["sale_amount", "customer_name"],
    "SALE_TRANSACTION": ["amount", "customer_name"],  # Add test case intent
    "TXN_PURCHASE": ["purchase_amount", "product_name"],
    "TXN_CREDIT_GIVEN": ["credit_amount", "customer_name"],
    "TXN_CREDIT_RECEIVED": ["credit_amount", "customer_name"],
    "TXN_EXPENSE": ["expense_amount", "expense_type"],

    # CRUD intents
    "CREATE_CUSTOMER": ["customer_name", "customer_phone"],
    "UPDATE_CUSTOMER": ["customer_id"],
    "CREATE_PRODUCT": ["product_name", "product_category", "product_price"],
    "UPDATE_PRODUCT": ["product_id"],
    "UPDATE_INVENTORY": ["product_id", "inventory_quantity"],
    "CREATE_EXPENSE": ["expense_amount", "expense_type", "occurred_at"],
    "UPDATE_EXPENSE": ["expense_id"],

    # Query intents (no required fields)
    "ASK_CASHFLOW_HEALTH": [],
    "ASK_FORECAST": [],
    "STOCK_INQUIRY": [],  # Add test case intent
    "ASK_CUSTOMER_KHATA": ["customer_name"],
    "ASK_INVENTORY": [],
    "ASK_TODAY_SALES": [],
    "ASK_COLLECTION_PRIORITY": [],
    "ASK_TOP_PRODUCTS": [],
    "ASK_CUSTOMER_ACTIVITY": ["customer_name"],
    "GET_TRANSACTIONS": [],
    "GET_CUSTOMERS": [],
    "GET_PRODUCTS": [],
    "GET_INVENTORY": [],
    "GET_EXPENSES": [],

    # Command intents
    "COMMAND_APPROVE_ACTION": [],
    "COMMAND_CANCEL": [],
}

# Auto-execution thresholds
AUTO_EXECUTE_CONFIDENCE_THRESHOLD = 0.85
MAX_AUTO_EXECUTE_AMOUNT = 10000.0  # ₹10,000 limit for auto-execution


class ValidationService:

    def validate_nlu_output(self, nlu_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate NLU output and compute missing fields
        Returns validated output with missing_fields computed
        """
        from app.services.nlu import NLUOutput

        try:
            # Step B: Validate against Pydantic schema
            validated_output = NLUOutput(**nlu_output)

            # Step C: Compute missing fields
            intent = validated_output.intent
            entities = validated_output.entities or {}

            required_fields = REQUIRED_FIELDS_BY_INTENT.get(intent, [])
            present_fields = set()

            # Check which required fields are present and non-null
            for field in required_fields:
                if field in entities and entities[field] is not None and str(entities[field]).strip():
                    present_fields.add(field)

            missing_fields = list(set(required_fields) - present_fields)

            # Step D: Determine if clarification needed
            needs_clarification = (
                len(missing_fields) > 0 or
                validated_output.confidence < AUTO_EXECUTE_CONFIDENCE_THRESHOLD or
                validated_output.needs_clarification
            )

            # Update output with computed fields
            result = validated_output.dict()
            result["missing_fields"] = missing_fields
            result["needs_clarification"] = needs_clarification
            result["is_valid"] = not needs_clarification and len(missing_fields) == 0

            # Generate clarification question if needed
            if needs_clarification and not result.get("clarification_question"):
                result["clarification_question"] = self._generate_clarification_question(
                    intent, missing_fields, validated_output.confidence
                )

            return result

        except ValidationError as e:
            logger.error(f"NLU output validation failed: {e}")
            return {
                "intent": "UNKNOWN",
                "entities": {},
                "confidence": 0.0,
                "needs_clarification": True,
                "clarification_question": "Kripya apna message clear kijiye. Main samajh nahi paya.",
                "missing_fields": [],
                "is_valid": False,
                "validation_error": str(e)
            }

    def can_auto_execute(self, validated_output: Dict[str, Any]) -> bool:
        """
        Determine if intent can be auto-executed without confirmation
        """
        # Check basic requirements
        if (validated_output.get("needs_clarification") or
            len(validated_output.get("missing_fields", [])) > 0 or
                validated_output.get("confidence", 0) < AUTO_EXECUTE_CONFIDENCE_THRESHOLD):
            return False

        # Check amount thresholds for financial transactions
        entities = validated_output.get("entities", {})
        for amount_field in ["sale_amount", "purchase_amount", "credit_amount", "expense_amount"]:
            if amount_field in entities:
                try:
                    amount = float(entities[amount_field])
                    if amount > MAX_AUTO_EXECUTE_AMOUNT:
                        return False
                except (ValueError, TypeError):
                    return False

        # Check for risk flags (to be implemented)
        risks = validated_output.get("risks", [])
        if risks:
            return False

        return True

    def requires_confirmation(self, validated_output: Dict[str, Any], resolved_entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if action requires user confirmation and return confirmation details
        """
        intent = validated_output.get("intent")
        entities = validated_output.get("entities", {})

        confirmation_needed = False
        confirmation_reason = ""
        confirmation_data = {}

        # Check for multiple candidates
        if resolved_entities.get("customer", {}).get("multiple_matches"):
            confirmation_needed = True
            confirmation_reason = "multiple_customers"
            confirmation_data = {
                "candidates": resolved_entities["customer"]["candidates"],
                "message": "Multiple customers found. Please select:"
            }

        # Check for high amounts
        for amount_field in ["sale_amount", "purchase_amount", "credit_amount", "expense_amount"]:
            if amount_field in entities:
                try:
                    amount = float(entities[amount_field])
                    if amount > MAX_AUTO_EXECUTE_AMOUNT:
                        confirmation_needed = True
                        confirmation_reason = "high_amount"
                        confirmation_data = {
                            "amount": amount,
                            "threshold": MAX_AUTO_EXECUTE_AMOUNT,
                            "message": f"High amount ₹{amount:,.2f} detected. Please confirm."
                        }
                except (ValueError, TypeError):
                    pass

        # Check for new customer creation
        if resolved_entities.get("customer", {}).get("created_new"):
            confirmation_needed = True
            confirmation_reason = "new_customer"
            confirmation_data = {
                "customer_name": resolved_entities["customer"]["name"],
                "message": f"New customer '{resolved_entities['customer']['name']}' will be created. Confirm?"
            }

        return {
            "needs_confirmation": confirmation_needed,
            "reason": confirmation_reason,
            "data": confirmation_data
        }

    def _generate_clarification_question(self, intent: str, missing_fields: List[str], confidence: float) -> str:
        """Generate appropriate clarification question based on missing fields"""

        if not missing_fields and confidence < AUTO_EXECUTE_CONFIDENCE_THRESHOLD:
            return "Kripya apna message clear kijiye. Main pura samajh nahi paya."

        if not missing_fields:
            return "Aur koi details chahiye?"

        # Intent-specific clarification questions
        clarification_messages = {
            "customer_name": "Customer ka naam bataiye?",
            "customer_phone": "Customer ka phone number bataiye?",
            "sale_amount": "Sale ka amount kitna hai?",
            "purchase_amount": "Purchase ka amount kitna hai?",
            "credit_amount": "Credit ka amount kitna hai?",
            "expense_amount": "Expense ka amount kitna hai?",
            "expense_type": "Expense ka type kya hai? (PURCHASE, OPERATING, FUEL, TRANSPORT, MISC)",
            "product_name": "Product ka naam bataiye?",
            "product_category": "Product ka category kya hai?",
            "product_price": "Product ka price kitna hai?",
            "inventory_quantity": "Kitna quantity hai?",
            "occurred_at": "Yeh kab hua tha? Date aur time bataiye.",
        }

        if len(missing_fields) == 1:
            field = missing_fields[0]
            return clarification_messages.get(field, f"{field} ki information chahiye.")

        # Multiple missing fields
        questions = []
        for field in missing_fields[:2]:  # Ask for max 2 fields at once
            if field in clarification_messages:
                questions.append(clarification_messages[field])

        if questions:
            return " ".join(questions)

        return f"Yeh details chahiye: {', '.join(missing_fields)}"


# Global validation service
validation_service = ValidationService()
