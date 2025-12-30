import logging
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
from app.graphs.nodes.intent_classifier import classify_intent, ChatState
from app.graphs.nodes.policy_qa import handle_policy_question
from app.graphs.nodes.leave_request_tool import handle_leave_request

logger = logging.getLogger(__name__)


def route_by_intent(state: ChatState) -> Literal["policy_qa", "leave_request"]:
    """Route to appropriate node based on intent"""
    intent = state.get("intent")
    logger.info(f"🔀 ROUTING: Intent = '{intent}'")
    
    if intent == "leave_request":
        logger.info("   → Routing to LEAVE_REQUEST node")
        return "leave_request"
    else:
        logger.info("   → Routing to POLICY_QA node")
        return "policy_qa"


def create_chat_graph():
    """Create and compile the chat graph"""
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("intent_classifier", classify_intent)
    workflow.add_node("policy_qa", handle_policy_question)
    workflow.add_node("leave_request", handle_leave_request)
    
    # Set entry point
    workflow.set_entry_point("intent_classifier")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "policy_qa": "policy_qa",
            "leave_request": "leave_request"
        }
    )
    
    # Both paths end
    workflow.add_edge("policy_qa", END)
    workflow.add_edge("leave_request", END)
    
    # Compile graph
    return workflow.compile()


# Create the graph instance
chat_graph = create_chat_graph()

