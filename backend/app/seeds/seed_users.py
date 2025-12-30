import sys
import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User
from app.database import SessionLocal


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def seed_users(db: Session):
    """Seed sample users for testing"""
    
    print("=" * 50)
    print("Starting user seeding process...")
    print("=" * 50)
    
    # Check if users already exist
    existing_count = db.query(User).count()
    print(f"Current user count in database: {existing_count}")
    
    if existing_count > 0:
        print("Users already exist in database. Skipping seed...")
        print("Existing users:")
        for user in db.query(User).all():
            print(f"  - {user.email} ({user.role})")
        return
    
    users_data = [
        {
            "email": "hr@company.com",
            "full_name": "Sarah HR Manager",
            "role": "HR",
            "password": "hr123456"  # Will be hashed
        },
        {
            "email": "john.employee@company.com",
            "full_name": "John Employee",
            "role": "employee",
            "password": "employee123"
        },
        {
            "email": "jane.employee@company.com",
            "full_name": "Jane Smith",
            "role": "employee",
            "password": "employee123"
        }
    ]
    
    print(f"\nPreparing to seed {len(users_data)} users...")
    
    for idx, user_data in enumerate(users_data, 1):
        print(f"\n[{idx}/{len(users_data)}] Processing user: {user_data['email']}")
        password = user_data.pop("password")
        print(f"  - Full name: {user_data['full_name']}")
        print(f"  - Role: {user_data['role']}")
        print(f"  - Hashing password...")
        
        password_hash = hash_password(password)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data['email']).first()
        if existing_user:
            print(f"  - WARNING: User with email {user_data['email']} already exists. Skipping...")
            continue
        
        user = User(
            **user_data,
            password_hash=password_hash
        )
        db.add(user)
        print(f"  - ✓ User added to session")
    
    print("\nCommitting changes to database...")
    try:
        db.commit()
        print("✓ Database commit successful!")
        
        # Verify users were created
        final_count = db.query(User).count()
        print(f"\nFinal user count in database: {final_count}")
        
        print("\n" + "=" * 50)
        print("Sample users seeded successfully!")
        print("=" * 50)
        print("\nLogin Credentials:")
        print("  HR User: hr@company.com / hr123456")
        print("  Employee Users:")
        print("    - john.employee@company.com / employee123")
        print("    - jane.employee@company.com / employee123")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to commit users to database: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    print("Initializing database connection...")
    db = SessionLocal()
    try:
        seed_users(db)
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
        print("\nDatabase connection closed.")

