import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from app.database import get_db
from app.models.chat_session import ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse
from app.api.auth import get_current_user
from app.graphs.chat_graph import chat_graph
from app.graphs.nodes.intent_classifier import ChatState

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    message_data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process chat message using LangGraph"""
    
    logger.info("=" * 60)
    logger.info("CHAT REQUEST RECEIVED")
    logger.info("=" * 60)
    logger.info(f"User: {current_user.email} (ID: {current_user.id}, Role: {current_user.role})")
    logger.info(f"Message: {message_data.message}")
    
    # Get or create session_id
    session_id = message_data.session_id or str(uuid.uuid4())
    logger.info(f"Session ID: {session_id}")
    
    # Retrieve conversation context from the last message in this session
    last_chat = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).first()
    
    conversation_context = None
    if last_chat and last_chat.conversation_data:
        conversation_context = last_chat.conversation_data
        logger.info(f"Loaded conversation context: {conversation_context}")
    
    # Initialize state (use authenticated user's ID, not from request)
    initial_state: ChatState = {
        "message": message_data.message,
        "user_id": current_user.id,  # Always use authenticated user
        "intent": None,
        "context": None,
        "tool_result": None,
        "response": "",
        "conversation_data": conversation_context  # Pass existing conversation context
    }
    logger.info("Initial state created, starting LangGraph orchestration...")
    
    # Run the graph
    try:
        logger.info(">>> Invoking LangGraph workflow")
        result = chat_graph.invoke(initial_state)
        logger.info("<<< LangGraph workflow completed")
        logger.info(f"Final intent: {result.get('intent')}")
        logger.info(f"Response length: {len(result.get('response', ''))} characters")
        if result.get('tool_result'):
            logger.info(f"Tool result: {result.get('tool_result')}")
        
        # Save to database
        logger.info("Saving chat session to database...")
        chat_session = ChatSession(
            session_id=session_id,
            user_id=current_user.id,
            message=message_data.message,
            response=result["response"],
            intent=result.get("intent"),
            conversation_data=result.get("conversation_data")  # Save conversation state
        )
        db.add(chat_session)
        db.commit()
        logger.info("Chat session saved successfully")
        
        # Prepare response
        response_data = {
            "response": result["response"],
            "intent": result.get("intent"),
            "data": result.get("tool_result"),
            "session_id": session_id
        }
        
        logger.info("=" * 60)
        logger.info("CHAT REQUEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return ChatResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

