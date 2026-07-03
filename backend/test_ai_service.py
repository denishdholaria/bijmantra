import asyncio
from app.core.database import AsyncSessionLocal
from app.modules.ai.service import get_ai_provider_service
from app.models.core import Organization
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Organization).where(Organization.name == "Demo Organization"))
        org = result.scalar_one_or_none()
        if not org:
            print("Demo org not found")
            return
            
        svc = get_ai_provider_service()
        registry = await svc.load_registry(db, org.id)
        
        print("--- All Providers in Registry ---")
        for k, v in registry.providers.items():
            print(f"{k.value}: available={v.available}")
            
        print("\n--- Available Providers for Dispatch ---")
        for p in registry.get_available():
            print(f"{p.provider.value} (model: {p.model})")

if __name__ == "__main__":
    asyncio.run(main())
