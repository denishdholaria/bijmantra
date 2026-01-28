"""
Create User Script

Interactive CLI script to create a new user account.
Usage: python -m app.scripts.create_user

This script:
1. Prompts for user details (email, name, password)
2. Creates or selects an organization
3. Creates the user with proper password hashing

NOTE: Uses synchronous SQLAlchemy because this is a CLI script,
not an async endpoint. Compliant with GOVERNANCE.md §4.3.1.
"""

import sys
import getpass
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, ""


def main():
    """Main entry point for create_user script"""
    from app.models.core import User, Organization
    
    print("\n=== BijMantra User Creation ===\n")
    
    # Create sync database connection
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Get email
        while True:
            email = input("Email: ").strip()
            if not email:
                print("Email is required")
                continue
            if not validate_email(email):
                print("Invalid email format")
                continue
            
            # Check if email exists
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                print(f"User with email {email} already exists")
                continue
            break
        
        # Get full name
        while True:
            full_name = input("Full Name: ").strip()
            if not full_name:
                print("Full name is required")
                continue
            break
        
        # Get password
        while True:
            password = getpass.getpass("Password: ")
            valid, msg = validate_password(password)
            if not valid:
                print(f"Invalid password: {msg}")
                continue
            
            confirm = getpass.getpass("Confirm Password: ")
            if password != confirm:
                print("Passwords do not match")
                continue
            break
        
        # Select or create organization
        print("\n--- Organization ---")
        orgs = db.query(Organization).filter(Organization.is_active == True).all()
        
        if orgs:
            print("Existing organizations:")
            for i, org in enumerate(orgs, 1):
                print(f"  {i}. {org.name}")
            print(f"  {len(orgs) + 1}. Create new organization")
            
            while True:
                choice = input(f"Select organization (1-{len(orgs) + 1}): ").strip()
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(orgs):
                        organization = orgs[choice_num - 1]
                        break
                    elif choice_num == len(orgs) + 1:
                        organization = None
                        break
                    else:
                        print("Invalid choice")
                except ValueError:
                    print("Please enter a number")
        else:
            organization = None
        
        # Create new organization if needed
        if organization is None:
            org_name = input("Organization Name: ").strip()
            if not org_name:
                org_name = f"{full_name}'s Organization"
            
            organization = Organization(
                name=org_name,
                description=f"Organization for {full_name}",
                contact_email=email,
                is_active=True,
            )
            db.add(organization)
            db.flush()
            print(f"Created organization: {org_name}")
        
        # Ask if superuser
        is_superuser = input("Make superuser? (y/N): ").strip().lower() == 'y'
        
        # Create user
        user = User(
            organization_id=organization.id,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=is_superuser,
        )
        db.add(user)
        db.commit()
        
        print(f"\n✓ User created successfully!")
        print(f"  Email: {email}")
        print(f"  Organization: {organization.name}")
        print(f"  Superuser: {'Yes' if is_superuser else 'No'}")
        
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
