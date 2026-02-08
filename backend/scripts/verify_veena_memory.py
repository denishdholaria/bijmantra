import asyncio
import sys
import os

# Set up path to backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.database import AsyncSessionLocal
from app.services.veena_service import VeenaService
from app.models.core import User
from sqlalchemy import select

async def verify_veena_memory():
    print("🧠 Awakening Veena Verification Protocol...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Get a Test User (Admin usually ID 1)
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ No users found in database!")
                return
            
            print(f"👤 Testing as User: {user.email}")
            
            # 2. Initialize Service
            veena = VeenaService(db)
            
            # 3. Test Context Creation
            print("📝 Checking User Context...")
            context = await veena.get_or_create_user_context(user)
            print(f"   ✅ Context Active (ID: {context.id})")
            print(f"   📊 Interaction Count: {context.total_interactions}")
            
            # 4. Test Memory Storage
            print("💾 Saving Test Memory...")
            await veena.save_episodic_memory(
                user=user,
                content="Verification Protocol 1660: System is ready.",
                source_type="verification",
                importance=0.9
            )
            await db.commit()
            print("   ✅ Memory Committed")
            
            # 5. Fetch Recent Memories
            print("🔍 Retrieving Memories...")
            memories = await veena.get_recent_memories(user.id, limit=1)
            if memories and "Verification Protocol 1660" in memories[0].content:
                print(f"   ✅ Retrieved: '{memories[0].content}'")
                print("🚀 VEENA COGNITIVE CORE IS OPERATIONAL")
            else:
                print("❌ Failed to retrieve memory")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(verify_veena_memory())
