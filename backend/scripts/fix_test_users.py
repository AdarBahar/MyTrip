#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.jwt import get_password_hash
from app.models.user import User, UserStatus


def fix_test_users():
    db = SessionLocal()

    try:
        # Test users with proper passwords
        test_users = [
            {
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test User",
            },
            {
                "email": "adar.bahar@gmail.com",
                "password": "mypassword",
                "display_name": "Adar Bahar",
            },
            {
                "email": "admin@mytrips.com",
                "password": "admin123",
                "display_name": "Admin User",
            },
        ]

        for user_data in test_users:
            # Check if user exists
            existing_user = (
                db.query(User).filter(User.email == user_data["email"]).first()
            )

            # Generate proper bcrypt hash
            password_hash = get_password_hash(user_data["password"])
            print(f"Generated hash for {user_data['email']}: {password_hash[:60]}...")

            if existing_user:
                # Update existing user with proper password hash
                existing_user.password_hash = password_hash
                existing_user.display_name = user_data["display_name"]
                existing_user.status = UserStatus.ACTIVE
                print(f"✅ Updated existing user: {user_data['email']}")
            else:
                # Create new user with proper password hash
                new_user = User(
                    email=user_data["email"],
                    display_name=user_data["display_name"],
                    password_hash=password_hash,
                    status=UserStatus.ACTIVE,
                )
                db.add(new_user)
                print(f"✅ Created new user: {user_data['email']}")

        db.commit()
        print("\n🎉 Test users fixed with proper password hashes!")
        print("\nTest credentials:")
        for user_data in test_users:
            print(f"  Email: {user_data['email']}")
            print(f"  Password: {user_data['password']}")
            print()

        # Verify the hashes work
        print("Verifying password hashes...")
        from app.core.jwt import verify_password

        for user_data in test_users:
            user = db.query(User).filter(User.email == user_data["email"]).first()
            if user and user.password_hash:
                is_valid = verify_password(user_data["password"], user.password_hash)
                print(
                    f"  {user_data['email']}: {'✅ Valid' if is_valid else '❌ Invalid'}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_test_users()
