from pydantic import BaseModel
from typing import Optional, Dict, Any


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    # user_id is not needed - comes from authenticated user


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    session_id: str

