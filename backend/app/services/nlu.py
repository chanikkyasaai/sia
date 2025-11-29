import re
import json
import logging
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from app.services.llm import llm_service
from app.services.prompts import NLU_SESSION_SYSTEM_PROMPT, NLU_USER_PROMPT_TEMPLATE, NLU_SESSION_SYSTEM_PROMPT, NLU_SESSION_USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class NLUOutput(BaseModel):
    intent: str
    entities: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_clarification: bool
    clarification_question: Optional[str] = None


async def parse_intent(transcript: str, business_id: int) -> NLUOutput:
    """Parse intent using LLM first with validation pipeline, fallback to rule-based approach"""

    from app.services.validation import validation_service

    # Try LLM first (gpt-4o-mini)
    try:
        user_prompt = NLU_USER_PROMPT_TEMPLATE.format(
            business_id=business_id,
            transcript=transcript
        )

        # Step A & B: LLM call with validation and retry logic
        llm_result = await _call_llm_with_validation(
            system_prompt=NLU_SESSION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_retries=2
        )

        if llm_result:
            # Step C & D: Validate and compute missing fields
            validated_result = validation_service.validate_nlu_output(
                llm_result)
            return NLUOutput(**validated_result)

    except Exception as e:
        logger.warning(f"LLM NLU failed, falling back to rules: {e}")

    # Rule-based fallback with comprehensive coverage
    result = _rule_based_parse(transcript)

    # Apply validation to rule-based result too
    try:
        validated_result = validation_service.validate_nlu_output(
            result.dict())
        return NLUOutput(**validated_result)
    except Exception as e:
        logger.error(f"Validation failed for rule-based result: {e}")
        return result


async def parse_intent_with_session(transcript: str, business_id: int, session_data: Dict[str, Any]) -> NLUOutput:
    """Parse intent using session context for multi-turn conversations"""

    try:
        from app.services.session import session_service
        from app.services.validation import validation_service

        conversation_context = session_service.get_conversation_context(
            session_data)
        parsed_state = json.dumps(session_data.get(
            "parsed_state", {}), ensure_ascii=False)

        # Create enhanced prompt for context-aware parsing
        user_prompt = f"""Business ID: {business_id}

Recent conversation:
{conversation_context}

Current user input: "{transcript}"

Previous parsed state:
{parsed_state}

CRITICAL: If the user is providing additional information (like amount, name, etc.) that completes a previous incomplete transaction, merge it with the previous context. For example:
- Previous: "I sold apples to Ravi" (missing amount)
- Current: "50 rupees" 
- Result: Complete TXN_SALE with sale_amount=50, customer_name=Ravi, product_name=apples

Output ONLY JSON with intent, entities (including merged context), confidence, and needs_clarification."""

        llm_result = await llm_service.call_mini_llm(
            system_prompt=NLU_SESSION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=400
        )

        if llm_result:
            # Validate and enhance the result
            validated_result = validation_service.validate_nlu_output(
                llm_result)
            return NLUOutput(**validated_result)

    except Exception as e:
        logger.warning(
            f"Session-aware LLM NLU failed, falling back to context-enhanced rule-based parse: {e}")

    # Enhanced fallback with context merging
    return _context_enhanced_parse(transcript, session_data, business_id)


def _rule_based_parse(transcript: str) -> NLUOutput:
    """Comprehensive rule-based NLU fallback"""
    transcript_lower = transcript.lower()
    intent = "UNKNOWN"
    entities = {}
    confidence = 0.6
    needs_clarification = False
    clarification_question = None

    # Transaction patterns
    if any(word in transcript_lower for word in ["becha", "bech", "sale", "sold", "बेचा", "बेच"]):
        intent = "TXN_SALE"
        amount = _extract_amount(transcript, ["ka", "का", "rupees", "rs"])
        if amount:
            entities["sale_amount"] = amount
            confidence = 0.8

    elif any(word in transcript_lower for word in ["udhaar", "credit", "udhar", "उधार", "क्रेडिट"]):
        intent = "TXN_CREDIT_GIVEN"
        amount = _extract_amount(
            transcript, ["udhaar", "credit", "udhar", "उधार"])
        if amount:
            entities["credit_amount"] = amount
            confidence = 0.8

    elif any(word in transcript_lower for word in ["kharida", "kharid", "purchase", "bought", "खरीदा", "खरीद"]):
        intent = "TXN_PURCHASE"
        amount = _extract_amount(transcript, ["ka", "का", "rupees", "rs"])
        if amount:
            entities["purchase_amount"] = amount
            confidence = 0.8

    elif any(word in transcript_lower for word in ["kharcha", "expense", "खर्चा", "व्यय"]):
        intent = "TXN_EXPENSE"
        amount = _extract_amount(transcript, ["ka", "का", "rupees", "rs"])
        if amount:
            entities["expense_amount"] = amount
            confidence = 0.8

    # Query patterns
    elif any(word in transcript_lower for word in ["kitna", "कितना", "how much", "balance", "बैलेंस"]):
        if any(word in transcript_lower for word in ["udhaar", "उधार", "credit", "khata", "खाता"]):
            intent = "ASK_CUSTOMER_KHATA"
            confidence = 0.9
        elif any(word in transcript_lower for word in ["aaj", "आज", "today", "sale", "बिक्री"]):
            intent = "ASK_TODAY_SALES"
            confidence = 0.9

    elif any(word in transcript_lower for word in ["stock", "स्टॉक", "inventory", "माल", "samaan", "सामान"]):
        intent = "ASK_INVENTORY"
        confidence = 0.8

    elif any(word in transcript_lower for word in ["cashflow", "cash flow", "पैसा", "रुपया"]):
        intent = "ASK_CASHFLOW_HEALTH"
        confidence = 0.8

    elif any(word in transcript_lower for word in ["collect", "वसूली", "vasuli", "payment", "पेमेंट"]):
        intent = "ASK_COLLECTION_PRIORITY"
        confidence = 0.8

    # Extract customer names
    customer_name = _extract_customer_name(transcript)
    if customer_name:
        entities["customer_name"] = customer_name

    # Extract product names
    product_name = _extract_product_name(transcript)
    if product_name:
        entities["product_name"] = product_name

    # If still unknown or low confidence, ask for clarification
    if intent == "UNKNOWN" or confidence < 0.6:
        needs_clarification = True
        clarification_question = "Kripya apna sawaal spasht karein. Aap kya janna chahte hain?"

    return NLUOutput(
        intent=intent,
        entities=entities,
        confidence=confidence,
        needs_clarification=needs_clarification,
        clarification_question=clarification_question
    )


def _extract_amount(transcript: str, keywords: list) -> Optional[float]:
    """Extract numeric amount from transcript near keywords"""
    for keyword in keywords:
        # Pattern: number + keyword
        pattern = rf"(\d+)\s*{re.escape(keyword)}"
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            return float(match.group(1))

        # Pattern: keyword + number
        pattern = rf"{re.escape(keyword)}\s*(\d+)"
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            return float(match.group(1))

    # General number extraction
    match = re.search(r"(\d+)", transcript)
    if match:
        return float(match.group(1))

    return None


def _extract_customer_name(transcript: str) -> Optional[str]:
    """Extract customer name from transcript"""
    # Common patterns: "Ramu ko", "Ramu ka", "to Ramu"
    patterns = [
        r"([A-Za-z]+)\s*ko",
        r"([A-Za-z]+)\s*ka",
        r"to\s+([A-Za-z]+)",
        r"([A-Za-z]+)\s*ke"
    ]

    for pattern in patterns:
        match = re.search(pattern, transcript, re.IGNORECASE)
        if match:
            name = match.group(1)
            if len(name) > 2:  # Filter out short words
                return name.title()

    return None


def _extract_product_name(transcript: str) -> Optional[str]:
    """Extract product name from transcript"""
    # Common product keywords
    common_products = [
        "parle g", "biscuit", "chai", "milk", "दूध", "चाय", "बिस्कुट",
        "rice", "चावल", "dal", "दाल", "oil", "तेल", "sugar", "चीनी"
    ]

    transcript_lower = transcript.lower()
    for product in common_products:
        if product in transcript_lower:
            return product.title()

    return None


async def _call_llm_with_validation(system_prompt: str, user_prompt: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """Call LLM with JSON validation and retry logic"""

    for attempt in range(max_retries + 1):
        try:
            llm_result = await llm_service.call_mini_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=400
            )

            if llm_result and isinstance(llm_result, dict):
                # Basic JSON validation - check required keys
                required_keys = {"intent", "entities",
                                 "confidence", "needs_clarification"}
                if required_keys.issubset(llm_result.keys()):
                    return llm_result
                else:
                    logger.warning(
                        f"LLM output missing required keys: {required_keys - llm_result.keys()}")

            # If validation failed and we have retries left
            if attempt < max_retries:
                error_msg = "Model output invalid: Missing required JSON fields. Produce only JSON with intent, entities, confidence, needs_clarification."
                user_prompt = f"{user_prompt}\n\n{error_msg}"
                continue

        except Exception as e:
            logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")

            if attempt < max_retries:
                continue

    logger.error(f"LLM validation failed after {max_retries + 1} attempts")
    return None


def _context_enhanced_parse(transcript: str, session_data: Dict[str, Any], business_id: int) -> NLUOutput:
    """Enhanced rule-based parsing that merges conversation context"""

    # First get basic rule-based parse
    basic_result = _rule_based_parse(transcript)

    # Check if we have conversation history to merge
    if not session_data or not session_data.get("turns"):
        return basic_result

    # Get the last few turns to understand context
    turns = session_data.get("turns", [])
    parsed_state = session_data.get("parsed_state", {})

    # Look for incomplete previous transactions
    last_user_turn = None
    for turn in reversed(turns):
        if turn.get("role") == "user":
            last_user_turn = turn.get("text", "")
            break

    if not last_user_turn:
        return basic_result

    # Check if current input might complete a previous transaction
    transcript_lower = transcript.lower()

    # If current input is just an amount and we have a previous incomplete sale
    if _is_amount_only(transcript) and "sold" in last_user_turn.lower():
        # Extract amount from current input
        amount = _extract_amount(transcript, ["rupees", "rs", ""])
        if amount:
            # Extract customer and product from previous turn
            customer_name = _extract_customer_name(last_user_turn)
            product_name = _extract_product_name(last_user_turn)

            # Create complete sale transaction
            return NLUOutput(
                intent="TXN_SALE",
                entities={
                    "sale_amount": amount,
                    "customer_name": customer_name,
                    "product_name": product_name
                },
                confidence=0.9,
                needs_clarification=False
            )

    # If current input is just a customer name and we have incomplete transaction
    elif _is_name_only(transcript) and any(word in last_user_turn.lower() for word in ["sold", "becha"]):
        # Extract amount from previous context if available
        prev_amount = _extract_amount(last_user_turn, ["rupees", "rs", ""])
        product_name = _extract_product_name(last_user_turn)

        return NLUOutput(
            intent="TXN_SALE",
            entities={
                "sale_amount": prev_amount,
                "customer_name": transcript.strip().title(),
                "product_name": product_name
            },
            confidence=0.85,
            needs_clarification=prev_amount is None
        )

    return basic_result


def _is_amount_only(transcript: str) -> bool:
    """Check if transcript contains only an amount"""
    # Remove common amount words
    cleaned = re.sub(r'\b(rupees?|rs|₹)\b', '', transcript.lower()).strip()
    # Check if remaining text is just numbers
    return bool(re.match(r'^\d+$', cleaned.strip()))


def _is_name_only(transcript: str) -> bool:
    """Check if transcript is likely just a person's name"""
    words = transcript.strip().split()
    # Simple heuristic: 1-2 capitalized words, no numbers
    return (len(words) <= 2 and
            all(word[0].isupper() for word in words if word) and
            not any(char.isdigit() for char in transcript))
