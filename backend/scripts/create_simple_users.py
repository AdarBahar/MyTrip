#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bcrypt
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserStatus
def hash_password(password: str) -> str:
   """Simple bcrypt password hashing"""
   password_bytes = password.encode('utf-8')
   salt = bcrypt.gensalt()
   hashed = bcrypt.hashpw(password_bytes, salt)
   return hashed.decode('utf-8')
def verify_password(password: str, hashed: str) -> bool:
   """Simple bcrypt password verification"""
   password_bytes = password.encode('utf-8')
   hashed_bytes = hashed.encode('utf-8')
   return bcrypt.checkpw(password_bytes, hashed_bytes)
def create_test_users():
   db = SessionLocal()

   try:
       # Test users with simple passwords
       test_users = [
           {"email": "test@example.com", "password": "password123", "display_name": "Test User"},
           {"email": "adar.bahar@gmail.com", "password": "mypassword", "display_name": "Adar Bahar"},
           {"email": "admin@mytrips.com", "password": "admin123", "display_name": "Admin User"}
       ]

       for user_data in test_users:
           # Generate bcrypt hash directly
           password_hash = hash_password(user_data["password"])
           print(f"Generated hash for {user_data['email']}: {password_hash[:30]}...")

           # Check if user exists
           existing_user = db.query(User).filter(User.email == user_data["email"]).first()

           if existing_user:
               # Update existing user
               existing_user.password_hash = password_hash
               existing_user.display_name = user_data["display_name"]
               existing_user.status = UserStatus.ACTIVE
               print(f"✅ Updated existing user: {user_data['email']}")
           else:
               # Create new user
               new_user = User(
                   email=user_data["email"],
                   display_name=user_data["display_name"],
                   password_hash=password_hash,
                   status=UserStatus.ACTIVE
               )
               db.add(new_user)
               print(f"✅ Created new user: {user_data['email']}")

       db.commit()
       print("\n🎉 Test users created with proper bcrypt hashes!")

       # Verify the hashes work
       print("\nVerifying password hashes...")
       for user_data in test_users:
           user = db.query(User).filter(User.email == user_data["email"]).first()
           if user and user.password_hash:
               is_valid = verify_password(user_data["password"], user.password_hash)
               print(f"  {user_data['email']}: {'✅ Valid' if is_valid else '❌ Invalid'}")

       print("\nTest credentials:")
       for user_data in test_users:
           print(f"  Email: {user_data['email']}")
           print(f"  Password: {user_data['password']}")
           print()

   except Exception as e:
       print(f"❌ Error: {e}")
       import traceback
       traceback.print_exc()
       db.rollback()
       raise
   finally:
       db.close()
if __name__ == "__main__":
   create_test_users()
