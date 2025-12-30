from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'HR' or 'employee'
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    hr_requests = relationship("HRRequest", back_populates="user", foreign_keys="HRRequest.user_id")
    reviewed_requests = relationship("HRRequest", back_populates="reviewer", foreign_keys="HRRequest.reviewed_by")
    chat_sessions = relationship("ChatSession", back_populates="user")


