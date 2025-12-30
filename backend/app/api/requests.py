from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.hr_request import HRRequest
from app.models.user import User
from app.schemas.hr_request import HRRequestResponse, HRRequestUpdate
from app.api.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[HRRequestResponse])
async def get_my_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's HR requests"""
    requests = db.query(HRRequest).filter(HRRequest.user_id == current_user.id).order_by(HRRequest.created_at.desc()).all()
    
    # Add user information to each request
    result = []
    for req in requests:
        req_dict = {
            **req.__dict__,
            "user_name": current_user.full_name,
            "user_email": current_user.email,
            "reviewed_by_name": None
        }
        # Get reviewer name if exists
        if req.reviewed_by:
            reviewer = db.query(User).filter(User.id == req.reviewed_by).first()
            if reviewer:
                req_dict["reviewed_by_name"] = reviewer.full_name
        result.append(HRRequestResponse.model_validate(req_dict))
    
    return result


@router.get("/all", response_model=List[HRRequestResponse])
async def get_all_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all HR requests (HR only)"""
    if current_user.role != "HR":
        raise HTTPException(status_code=403, detail="Only HR users can view all requests")
    
    # Join with User table to get employee information
    requests = db.query(HRRequest).join(User, HRRequest.user_id == User.id).order_by(HRRequest.created_at.desc()).all()
    
    # Add user and reviewer information to each request
    result = []
    for req in requests:
        # Get employee info
        employee = db.query(User).filter(User.id == req.user_id).first()
        
        req_dict = {
            **req.__dict__,
            "user_name": employee.full_name if employee else None,
            "user_email": employee.email if employee else None,
            "reviewed_by_name": None
        }
        
        # Get reviewer name if exists
        if req.reviewed_by:
            reviewer = db.query(User).filter(User.id == req.reviewed_by).first()
            if reviewer:
                req_dict["reviewed_by_name"] = reviewer.full_name
        
        result.append(HRRequestResponse.model_validate(req_dict))
    
    return result


@router.patch("/{request_id}/approve", response_model=HRRequestResponse)
async def approve_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a leave request (HR only)"""
    if current_user.role != "HR":
        raise HTTPException(status_code=403, detail="Only HR users can approve requests")
    
    request = db.query(HRRequest).filter(HRRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "approved"
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    return HRRequestResponse.model_validate(request)


@router.patch("/{request_id}/reject", response_model=HRRequestResponse)
async def reject_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a leave request (HR only)"""
    if current_user.role != "HR":
        raise HTTPException(status_code=403, detail="Only HR users can reject requests")
    
    request = db.query(HRRequest).filter(HRRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "rejected"
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    return HRRequestResponse.model_validate(request)

