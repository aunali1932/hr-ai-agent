from pydantic import BaseModel, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    # user_id is not needed - comes from authenticated user


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    session_id: str


class ChatHistoryItem(BaseModel):
    id: int
    message: str
    response: str
    intent: Optional[str] = None
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat()
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatHistoryItem]

