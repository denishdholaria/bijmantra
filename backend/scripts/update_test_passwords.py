#!/usr/bin/env python3
"""
Update test user passwords to match expected E2E test credentials.

This script updates the passwords for demo and admin users to ensure
E2E tests can authenticate properly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.security import get_password_hash

def main():
    # Connect to database - use sync driver for this script
    db_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(db_url)

    # Password updates
    updates = [
        ("demo@bijmantra.org", "Demo123!"),
        ("admin@bijmantra.org", "Admin123!"),
    ]

    with engine.connect() as conn:
        for email, password in updates:
            hashed = get_password_hash(password)
            result = conn.execute(
                text("UPDATE users SET hashed_password = :hash WHERE email = :email"),
                {"hash": hashed, "email": email}
            )
            if result.rowcount > 0:
                print(f"✅ Updated password for {email}")
            else:
                print(f"⚠️ User {email} not found")
        conn.commit()

    print("\n✅ Password update complete")

if __name__ == "__main__":
    main()
