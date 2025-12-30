import logging
from typing import TypedDict, Optional
from app.services.gemini_service import get_gemini_model
import json

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    message: str
    user_id: int
    intent: Optional[str]
    context: Optional[str]
    tool_result: Optional[dict]
    response: str
    conversation_data: Optional[dict]  # Store conversation state for multi-turn conversations


def classify_intent(state: ChatState) -> ChatState:
    """Classify user message intent using Gemini"""
    logger.info("📋 NODE: Intent Classifier")
    logger.info(f"   Input message: {state['message']}")
    
    # Check if there's an ongoing leave request conversation
    conversation_data = state.get("conversation_data")
    if conversation_data and conversation_data.get("flow") == "leave_request":
        logger.info("   ✓ Continuing existing leave request conversation")
        state["intent"] = "leave_request"
        return state
    
    message = state["message"]
    
    prompt = f"""You are an intent classifier for an HR AI agent. Classify the following user message into one of two categories:
1. "policy_question" - User is asking about HR policies (e.g., "What is the work from home policy?", "How many sick days do I get?")
2. "leave_request" - User wants to create a leave request (e.g., "I need to take leave", "Apply for annual leave", "I need a sick day")

User message: {message}

Respond with ONLY a JSON object in this exact format:
{{"intent": "policy_question" or "leave_request"}}

Do not include any other text or explanation."""

    logger.info("   Calling Gemini for intent classification...")
    model = get_gemini_model()
    response = model.generate_content(prompt)
    logger.info(f"   Gemini raw response: {response.text[:200]}...")
    
    try:
        # Extract JSON from response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        intent_data = json.loads(response_text)
        intent = intent_data.get("intent", "policy_question")
        
        # Validate intent
        if intent not in ["policy_question", "leave_request"]:
            logger.warning(f"   Invalid intent '{intent}', defaulting to 'policy_question'")
            intent = "policy_question"  # Default fallback
        else:
            logger.info(f"   ✓ Classified intent: '{intent}'")
    except Exception as e:
        logger.error(f"   ✗ Error classifying intent: {e}")
        intent = "policy_question"  # Default fallback
    
    state["intent"] = intent
    logger.info(f"   Node output: intent = '{intent}'")
    return state

