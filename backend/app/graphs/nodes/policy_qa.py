import logging
from typing import TypedDict, Optional
from app.services.gemini_service import get_gemini_model
from app.services.rag_service import get_rag_context

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    message: str
    user_id: int
    intent: Optional[str]
    context: Optional[str]
    tool_result: Optional[dict]
    response: str


def handle_policy_question(state: ChatState) -> ChatState:
    """Handle policy question using RAG"""
    logger.info("📚 NODE: Policy Q&A (RAG)")
    logger.info(f"   User question: {state['message']}")
    
    message = state["message"]
    
    # Get relevant context from RAG
    logger.info("   Retrieving relevant policy chunks from Qdrant...")
    context = get_rag_context(message, top_k=3)
    logger.info(f"   Retrieved context length: {len(context)} characters")
    if context:
        logger.info(f"   Context preview: {context[:200]}...")
    else:
        logger.warning("   ⚠ No context retrieved from RAG")
    
    # Generate answer using Gemini with context
    prompt = f"""You are a helpful HR assistant. Answer the user's question about company HR policies based on the following context from policy documents.

Context from HR Policies:
{context}

User Question: {message}

Provide a clear, helpful answer based on the context. If the context doesn't contain enough information, say so politely. Be conversational and friendly."""

    logger.info("   Generating answer with Gemini...")
    model = get_gemini_model()
    response = model.generate_content(prompt)
    logger.info(f"   ✓ Answer generated ({len(response.text)} characters)")
    
    state["context"] = context
    state["response"] = response.text
    logger.info("   Node completed successfully")
    return state

