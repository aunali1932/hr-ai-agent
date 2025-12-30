import logging
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.hr_request import HRRequest

logger = logging.getLogger(__name__)


def create_leave_request(
    user_id: int,
    start_date: str,
    end_date: str,
    request_type: str,
    duration_days: int,
    reason: str = None
) -> dict:
    """Create a leave request in the database"""
    logger.info(f"🔧 TOOL: create_leave_request")
    logger.info(f"   Parameters: user_id={user_id}, type={request_type}, dates={start_date} to {end_date}, days={duration_days}")
    
    db: Session = SessionLocal()
    
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        logger.info(f"   Parsed dates: start={start}, end={end}")
        
        # Create HR request
        logger.info("   Creating HRRequest object...")
        hr_request = HRRequest(
            user_id=user_id,
            request_type=request_type,
            start_date=start,
            end_date=end,
            duration_days=duration_days,
            reason=reason,
            status="pending"
        )
        
        logger.info("   Adding to database session...")
        db.add(hr_request)
        logger.info("   Committing to database...")
        db.commit()
        db.refresh(hr_request)
        logger.info(f"   ✓ Leave request created successfully: ID={hr_request.id}")
        
        result = {
            "id": hr_request.id,
            "user_id": hr_request.user_id,
            "request_type": hr_request.request_type,
            "start_date": str(hr_request.start_date),
            "end_date": str(hr_request.end_date),
            "duration_days": hr_request.duration_days,
            "status": hr_request.status,
            "created_at": hr_request.created_at.isoformat() if hr_request.created_at else None
        }
        logger.info(f"   Tool result: {result}")
        return result
    except Exception as e:
        logger.error(f"   ✗ Error creating leave request: {e}", exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()
        logger.info("   Database session closed")

