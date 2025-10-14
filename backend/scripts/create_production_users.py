#!/usr/bin/env python3
"""
Script to create production users with passwords
Run this after deploying to production to set up initial users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserStatus
from app.core.jwt import get_password_hash


def create_production_users():
    """Create production users with passwords"""
    db = SessionLocal()
    
    try:
        # Production users to create
        production_users = [
            {
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test User"
            },
            {
                "email": "adar.bahar@gmail.com", 
                "password": "admin123",
                "display_name": "Adar Bahar"
            },
            {
                "email": "admin@mytrips.com",
                "password": "admin123",
                "display_name": "Admin User"
            }
        ]
        
        for user_data in production_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing_user:
                # Update existing user with password
                existing_user.password_hash = get_password_hash(user_data["password"])
                existing_user.display_name = user_data["display_name"]
                existing_user.status = UserStatus.ACTIVE
                print(f"✅ Updated existing user: {user_data['email']}")
            else:
                # Create new user
                new_user = User(
                    email=user_data["email"],
                    display_name=user_data["display_name"],
                    password_hash=get_password_hash(user_data["password"]),
                    status=UserStatus.ACTIVE
                )
                db.add(new_user)
                print(f"✅ Created new user: {user_data['email']}")
        
        db.commit()
        print("\n🎉 Production users created/updated successfully!")
        print("\nProduction credentials:")
        for user_data in production_users:
            print(f"  Email: {user_data['email']}")
            print(f"  Password: {user_data['password']}")
            print()
        
        # Verify the hashes work
        print("Verifying password hashes...")
        from app.core.jwt import verify_password
        for user_data in production_users:
            user = db.query(User).filter(User.email == user_data["email"]).first()
            if user and user.password_hash:
                is_valid = verify_password(user_data["password"], user.password_hash)
                print(f"  {user_data['email']}: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
    except Exception as e:
        print(f"❌ Error creating production users: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_production_users()
