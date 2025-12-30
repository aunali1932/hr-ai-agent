from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import date, datetime


class HRRequestBase(BaseModel):
    request_type: str
    start_date: date
    end_date: date
    duration_days: int
    reason: Optional[str] = None


class HRRequestCreate(HRRequestBase):
    pass


class HRRequestResponse(HRRequestBase):
    id: int
    user_id: int
    user_name: Optional[str] = None  # Employee name
    user_email: Optional[str] = None  # Employee email
    status: str
    reviewed_by: Optional[int] = None
    reviewed_by_name: Optional[str] = None  # Reviewer name
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @field_serializer('created_at', 'reviewed_at')
    def serialize_datetime(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        return dt.isoformat()
    
    @field_serializer('start_date', 'end_date')
    def serialize_date(self, d: date, _info):
        return d.isoformat()
    
    class Config:
        from_attributes = True


class HRRequestUpdate(BaseModel):
    status: str
    reviewed_by: int

