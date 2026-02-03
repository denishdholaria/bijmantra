
import asyncio
import sys
import os
import traceback
from datetime import date

# Ensure backend directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from sqlalchemy import select, update
    from app.core.database import async_session_maker
    from app.models.core import Organization, User
    from app.models.ai_quota import AIUsageDaily
    from app.services.ai.quota import AIQuotaService
    from fastapi import HTTPException
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    print(f"sys.path is: {sys.path}")
    sys.exit(1)

async def verify_quota_system():
    print("🧪 Starting AI Quota System Verification...")
    
    try:
        async with async_session_maker() as db:
            # 1. Setup Test Organization
            print("   [1/4] Setting up test environment...")
            
            # Get first organization
            stmt_org = select(Organization).limit(1)
            result = await db.execute(stmt_org)
            org = result.scalar_one_or_none()
            
            if not org:
                print("❌ No organization found to test.")
                return

            print(f"      - Testing with Organization ID: {org.id}")
            
            # Reset Usage for today
            stmt_reset = update(AIUsageDaily).where(
                AIUsageDaily.organization_id == org.id,
                AIUsageDaily.usage_date == date.today()
            ).values(request_count=0)
            await db.execute(stmt_reset)
            
            # Set Limit to 3 for testing
            original_limit = org.ai_daily_limit
            org.ai_daily_limit = 3
            db.add(org)
            await db.commit()
            print("      - Limit set to 3 requests.")

            # 2. Simulate Requests (Success Case)
            print("   [2/4] Simulating allowed requests...")
            for i in range(3):
                allowed = await AIQuotaService.check_and_increment_usage(
                    db, org.id, increment=True
                )
                print(f"      - Request {i+1}: {'Allowed ✅' if allowed else 'Blocked ❌'}")
                if not allowed:
                    raise Exception("Should have been allowed!")

            # 3. Simulate Requests (Blocked Case)
            print("   [3/4] Simulating blocked request (Over Limit)...")
            try:
                await AIQuotaService.check_and_increment_usage(
                    db, org.id, increment=True
                )
                print("❌ Request 4 was ALLOWED (Should have failed!)")
            except HTTPException as e:
                # Need to check status code properly
                if e.status_code == 429:
                    print("      - Request 4: Blocked (429) ✅")
                else:
                    print(f"❌ Wrong error code: {e.status_code}")
            except Exception as e:
                print(f"❌ Unexpected error in block phase: {type(e)} - {e}")

            # 4. Check API Stats
            print("   [4/4] Verifying Stats API data...")
            stats = await AIQuotaService.get_usage_stats(db, org.id)
            print(f"      - Stats: {stats}")
            if stats['used'] == 3 and stats['remaining'] == 0:
                 print("      - Stats Match ✅")
            else:
                 print("❌ Stats mismatch!")

            # Cleanup
            org.ai_daily_limit = original_limit
            db.add(org)
            await db.commit()
            print("\n✅ Verification Complete. System restored.")

    except Exception as e:
        print("\n❌ CRITICAL FAILURE IN SCRIPT:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_quota_system())
