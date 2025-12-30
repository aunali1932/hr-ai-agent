"""
Initialize database: run migrations, seed users, and ingest policies
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine
from app.models import Base
from app.seeds.seed_users import seed_users
from app.services.rag_service import ingest_policy_documents

def init_database():
    """Initialize database with migrations, seeds, and policy ingestion"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Seeding users...")
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()
    
    print("Ingesting HR policies into Qdrant...")
    try:
        ingest_policy_documents()
        print("✓ Database initialization complete!")
    except Exception as e:
        print(f"Error ingesting policies: {e}")
        print("Make sure Qdrant is running and GEMINI_API_KEY is set")

if __name__ == "__main__":
    init_database()


