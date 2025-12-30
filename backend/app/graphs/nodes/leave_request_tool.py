import logging
from typing import TypedDict, Optional
from datetime import datetime, date, timedelta
from app.services.gemini_service import get_gemini_model
from app.graphs.tools.create_leave_request import create_leave_request
import json

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    message: str
    user_id: int
    intent: Optional[str]
    context: Optional[str]
    tool_result: Optional[dict]
    response: str
    conversation_data: Optional[dict]


def extract_from_message(message: str, extract_type: str) -> Optional[str]:
    """Extract specific information from user message using Gemini"""
    
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    if extract_type == "leave_type":
        # First, check if it's a numeric choice (1, 2, 3)
        message_stripped = message.strip().lower()
        
        # Handle numeric inputs
        if message_stripped == "1" or message_stripped == "1.":
            return "sick"
        elif message_stripped == "2" or message_stripped == "2.":
            return "annual"
        elif message_stripped == "3" or message_stripped == "3.":
            return "parental"
        
        # Handle direct keyword matches (case-insensitive)
        if "sick" in message_stripped:
            return "sick"
        elif "annual" in message_stripped or "vacation" in message_stripped or "holiday" in message_stripped:
            return "annual"
        elif "parental" in message_stripped or "maternity" in message_stripped or "paternity" in message_stripped:
            return "parental"
        
        # If not a simple match, use Gemini to extract
        prompt = f"""Extract the leave type from the user's message. 
        
Valid leave types are:
- "sick" (for sick leave, medical leave, illness)
- "annual" (for vacation, annual leave, holiday)
- "parental" (for parental leave, maternity, paternity)

User message: {message}

If you can identify the leave type, respond with ONLY one word: "sick", "annual", or "parental"
If you cannot determine the leave type, respond with "unknown"

Respond with ONLY the leave type, no other text."""

    elif extract_type == "dates":
        prompt = f"""Extract start and end dates from the user's message.

TODAY'S DATE: {today_str}
TOMORROW'S DATE: {tomorrow}

User message: {message}

Return ONLY a JSON object with this structure:
{{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}

Rules:
- If only one date is mentioned, use it for both start_date and end_date (single day)
- If "today" is mentioned, use {today_str}
- If "tomorrow" is mentioned, use {tomorrow}
- If "next week Monday" is mentioned, calculate from {today_str}
- All dates MUST be in YYYY-MM-DD format
- If you cannot determine dates, respond with: {{"start_date": "unknown", "end_date": "unknown"}}

Respond with ONLY the JSON object, no other text."""

    elif extract_type == "reason":
        prompt = f"""Extract the reason for leave from the user's message.

User message: {message}

Provide a brief, clear reason (1-2 sentences). If the user provided a reason, use it. If not clear, respond with "Personal reasons".

Respond with ONLY the reason text, no other formatting."""

    else:
        return None

    try:
        model = get_gemini_model()
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return response_text
    except Exception as e:
        logger.error(f"Error extracting {extract_type}: {e}")
        return None


def handle_leave_request(state: ChatState) -> ChatState:
    """Handle leave request with conversational flow"""
    logger.info("🛠️  NODE: Leave Request Tool (Conversational)")
    logger.info(f"   User ID: {state['user_id']}")
    logger.info(f"   Message: {state['message']}")
    
    message = state["message"].lower().strip()
    conversation_data = state.get("conversation_data") or {}
    
    # Initialize conversation data if this is a new leave request
    if not conversation_data.get("flow"):
        logger.info("   Starting NEW leave request conversation")
        conversation_data = {
            "flow": "leave_request",
            "stage": "ask_type",
            "data": {}
        }
    
    logger.info(f"   Current stage: {conversation_data.get('stage')}")
    logger.info(f"   Collected data: {conversation_data.get('data')}")
    
    stage = conversation_data.get("stage")
    collected_data = conversation_data.get("data", {})
    
    # Stage 1: Ask for leave type (and try to extract everything from initial message)
    if stage == "ask_type":
        # Try to extract ALL information from the initial message
        leave_type = extract_from_message(state["message"], "leave_type")
        dates_text = None
        
        if leave_type and leave_type in ["sick", "annual", "parental"]:
            logger.info(f"   ✓ Leave type detected: {leave_type}")
            collected_data["leave_type"] = leave_type
            
            # Also try to extract dates from the same message
            dates_text = extract_from_message(state["message"], "dates")
            
            try:
                if dates_text:
                    dates = json.loads(dates_text)
                    start_date_str = dates.get("start_date")
                    end_date_str = dates.get("end_date")
                    
                    if start_date_str != "unknown" and end_date_str != "unknown":
                        # Validate dates
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                        today = date.today()
                        
                        if start_date < today:
                            logger.info("   ✗ Start date is in the past")
                            conversation_data["stage"] = "ask_dates"
                            conversation_data["data"] = collected_data
                            state["conversation_data"] = conversation_data
                            state["response"] = f"Got it! You'd like to request {leave_type} leave. However, the start date cannot be in the past. Please provide a date that is today or in the future."
                            return state
                        
                        if end_date < start_date:
                            logger.info("   ✗ End date before start date")
                            conversation_data["stage"] = "ask_dates"
                            conversation_data["data"] = collected_data
                            state["conversation_data"] = conversation_data
                            state["response"] = f"Got it! You'd like to request {leave_type} leave. However, the end date cannot be before the start date. Please provide valid dates."
                            return state
                        
                        # Dates are valid! Skip to asking for reason
                        logger.info(f"   ✓ Dates also detected: {start_date_str} to {end_date_str}")
                        collected_data["start_date"] = start_date_str
                        collected_data["end_date"] = end_date_str
                        collected_data["duration_days"] = (end_date - start_date).days + 1
                        conversation_data["stage"] = "ask_reason"
                        conversation_data["data"] = collected_data
                        state["conversation_data"] = conversation_data
                        state["response"] = f"Perfect! I've got your {leave_type} leave request from {start_date_str} to {end_date_str} ({collected_data['duration_days']} day(s)). Could you please provide a brief reason for your leave?"
                        return state
            except Exception as e:
                logger.info(f"   Could not parse dates from initial message: {e}")
            
            # Leave type found but no valid dates - ask for dates
            conversation_data["stage"] = "ask_dates"
            conversation_data["data"] = collected_data
            state["conversation_data"] = conversation_data
            state["response"] = f"Got it! You'd like to request {leave_type} leave. When would you like to take this leave? Please provide the start date and end date (or just one date if it's a single day)."
        else:
            # No leave type detected - ask for it
            logger.info("   Could not detect leave type, asking user...")
            conversation_data["stage"] = "collect_type"  # Move to collection stage
            state["conversation_data"] = conversation_data
            state["response"] = "I'd be happy to help you request leave! What type of leave would you like to request?\n\n1. 🤒 Sick Leave\n2. 🏖️ Annual Leave\n3. 👶 Parental Leave\n\nPlease let me know which type."
        
        return state
    
    # Stage 2: Collect leave type (and check if dates are also provided)
    elif stage == "collect_type":
        leave_type = extract_from_message(state["message"], "leave_type")
        
        if leave_type and leave_type in ["sick", "annual", "parental"]:
            logger.info(f"   ✓ Leave type collected: {leave_type}")
            collected_data["leave_type"] = leave_type
            
            # Also check if user provided dates in this message
            dates_text = extract_from_message(state["message"], "dates")
            
            try:
                if dates_text:
                    dates = json.loads(dates_text)
                    start_date_str = dates.get("start_date")
                    end_date_str = dates.get("end_date")
                    
                    if start_date_str != "unknown" and end_date_str != "unknown":
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                        today = date.today()
                        
                        if start_date >= today and end_date >= start_date:
                            # Valid dates! Skip to reason
                            logger.info(f"   ✓ Dates also provided: {start_date_str} to {end_date_str}")
                            collected_data["start_date"] = start_date_str
                            collected_data["end_date"] = end_date_str
                            collected_data["duration_days"] = (end_date - start_date).days + 1
                            conversation_data["stage"] = "ask_reason"
                            conversation_data["data"] = collected_data
                            state["conversation_data"] = conversation_data
                            state["response"] = f"Great! I've got your {leave_type} leave from {start_date_str} to {end_date_str} ({collected_data['duration_days']} day(s)). Could you please provide a brief reason?"
                            return state
            except Exception as e:
                logger.info(f"   Could not parse dates: {e}")
            
            # Leave type collected but no valid dates
            conversation_data["stage"] = "ask_dates"
            conversation_data["data"] = collected_data
            state["conversation_data"] = conversation_data
            state["response"] = f"Perfect! When would you like to take your {leave_type} leave? Please provide the start date and end date (or just one date if it's a single day)."
        else:
            logger.info("   ✗ Could not understand leave type, asking again...")
            state["conversation_data"] = conversation_data
            state["response"] = "I didn't quite catch that. Please choose one of:\n\n1. Sick Leave\n2. Annual Leave\n3. Parental Leave"
        
        return state
    
    # Stage 3: Ask for dates
    elif stage == "ask_dates":
        dates_text = extract_from_message(state["message"], "dates")
        
        try:
            dates = json.loads(dates_text)
            start_date_str = dates.get("start_date")
            end_date_str = dates.get("end_date")
            
            if start_date_str != "unknown" and end_date_str != "unknown":
                # Validate dates
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                today = date.today()
                
                if start_date < today:
                    logger.info("   ✗ Start date is in the past")
                    state["conversation_data"] = conversation_data
                    state["response"] = "The start date cannot be in the past. Please provide a date that is today or in the future."
                    return state
                
                if end_date < start_date:
                    logger.info("   ✗ End date before start date")
                    state["conversation_data"] = conversation_data
                    state["response"] = "The end date cannot be before the start date. Please provide valid dates."
                    return state
                
                logger.info(f"   ✓ Dates collected: {start_date_str} to {end_date_str}")
                collected_data["start_date"] = start_date_str
                collected_data["end_date"] = end_date_str
                collected_data["duration_days"] = (end_date - start_date).days + 1
                conversation_data["stage"] = "ask_reason"
                conversation_data["data"] = collected_data
                state["conversation_data"] = conversation_data
                
                state["response"] = f"Great! I've noted that you need leave from {start_date_str} to {end_date_str} ({collected_data['duration_days']} day(s)). Could you please provide a brief reason for your leave request?"
            else:
                logger.info("   ✗ Could not extract dates")
                state["conversation_data"] = conversation_data
                state["response"] = "I couldn't understand the dates. Please provide them in a clear format, for example:\n- 'January 15 to January 20'\n- 'Tomorrow'\n- '2025-01-15 to 2025-01-20'"
        
        except Exception as e:
            logger.error(f"   ✗ Error parsing dates: {e}")
            state["conversation_data"] = conversation_data
            state["response"] = "I had trouble understanding those dates. Could you please provide them again? For example: 'January 15 to January 20' or 'tomorrow for 3 days'"
        
        return state
    
    # Stage 4: Ask for reason
    elif stage == "ask_reason":
        reason = extract_from_message(state["message"], "reason")
        
        if reason:
            logger.info(f"   ✓ Reason collected: {reason}")
            collected_data["reason"] = reason
            conversation_data["stage"] = "confirm"
            conversation_data["data"] = collected_data
            state["conversation_data"] = conversation_data
            
            # Show confirmation
            leave_type = collected_data["leave_type"].title()
            start_date = collected_data["start_date"]
            end_date = collected_data["end_date"]
            duration = collected_data["duration_days"]
            
            state["response"] = f"""Perfect! Let me confirm your leave request details:

📋 **Leave Request Summary**
- Type: {leave_type} Leave
- Start Date: {start_date}
- End Date: {end_date}
- Duration: {duration} day(s)
- Reason: {reason}

Is this correct? Please reply 'yes' to submit or 'no' to cancel."""
        else:
            logger.info("   ✗ Could not extract reason")
            state["conversation_data"] = conversation_data
            state["response"] = "Could you please provide a reason for your leave?"
        
        return state
    
    # Stage 5: Confirmation
    elif stage == "confirm":
        user_response = message.strip().lower()
        
        if user_response in ["yes", "y", "confirm", "correct", "submit", "ok", "okay", "sure"]:
            logger.info("   ✓ User confirmed, creating leave request...")
            
            try:
                result = create_leave_request(
                    user_id=state["user_id"],
                    start_date=collected_data["start_date"],
                    end_date=collected_data["end_date"],
                    request_type=collected_data["leave_type"],
                    duration_days=collected_data["duration_days"],
                    reason=collected_data.get("reason")
                )
                
                logger.info(f"   ✓ Leave request created: ID={result.get('id')}")
                
                # Clear conversation data
                state["conversation_data"] = None
                state["tool_result"] = result
                
                state["response"] = f"""✅ Your leave request has been submitted successfully!

**Request Details:**
- Type: {collected_data['leave_type'].title()} Leave
- Dates: {collected_data['start_date']} to {collected_data['end_date']}
- Duration: {collected_data['duration_days']} day(s)
- Status: Pending HR Approval

Your request will be reviewed by HR and you'll be notified of the decision soon. Is there anything else I can help you with?"""
                
            except Exception as e:
                logger.error(f"   ✗ Error creating leave request: {e}")
                state["conversation_data"] = None
                state["response"] = "I'm sorry, there was an error submitting your leave request. Please try again or contact HR directly."
        
        elif user_response in ["no", "n", "cancel", "nevermind", "nope"]:
            logger.info("   ✗ User cancelled leave request")
            state["conversation_data"] = None
            state["response"] = "No problem! Your leave request has been cancelled. Let me know if you need anything else."
        
        else:
            logger.info("   ? Unclear confirmation response")
            state["conversation_data"] = conversation_data
            state["response"] = "I didn't quite understand that. Please reply 'yes' to submit your leave request or 'no' to cancel."
        
        return state
    
    # Fallback
    else:
        logger.warning(f"   ⚠️ Unknown stage: {stage}")
        state["conversation_data"] = None
        state["response"] = "I'm sorry, something went wrong with the conversation. Let's start over. Would you like to request leave?"
        return state
