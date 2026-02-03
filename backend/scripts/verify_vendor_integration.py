import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Install/Ensure dependencies
try:
    import httpx
    import aiosqlite
    import geoalchemy2
except ImportError:
    print("Installing missing dependencies...")
    os.system("pip install httpx aiosqlite geoalchemy2")
    import httpx
    import aiosqlite
    import geoalchemy2

# Mock geoalchemy2 admin hooks to prevent Spatialite errors
# This must be done BEFORE creating tables
with patch("geoalchemy2.admin.select_dialect") as mock_select_dialect:
    # Mock the returned dialect object and its after_create method
    mock_dialect = MagicMock()
    mock_dialect.after_create = MagicMock()
    mock_select_dialect.return_value = mock_dialect

    from httpx import AsyncClient, ASGITransport
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    # Setup in-memory DB engine
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(class_=AsyncSession, autocommit=False, autoflush=False, bind=test_engine)

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    # Configure settings to use SQLite
    import app.core.config
    app.core.config.settings.USE_SQLITE = True

    # Patch create_async_engine to return our test_engine when app.core.database is imported
    # This avoids issues with Postgres-specific arguments
    with patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=test_engine):

        # Mock Redis
        sys.modules["app.core.redis"] = MagicMock()
        sys.modules["app.core.redis.redis_client"] = MagicMock()

        # Mock meilisearch
        sys.modules["app.core.meilisearch"] = MagicMock()

        # Mock task_queue
        sys.modules["app.services.task_queue"] = MagicMock()

        from app.main import app
        from app.core.database import Base, get_db

        # Import models
        from app.models.genotyping import VendorOrder
        from app.models.core import Organization, User
        from app.api.v2.dependencies import get_current_user

        # Override dependencies
        app.dependency_overrides[get_db] = override_get_db

        async def override_get_current_user():
            # Create a mock user
            return User(id=1, organization_id=1, email="test@bijmantra.org", full_name="Test User")

        app.dependency_overrides[get_current_user] = override_get_current_user

        async def verify():
            print("Creating tables...")
            # We are inside the patch context, so create_all should work without triggering geoalchemy errors
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            print("Seeding database...")
            async with TestingSessionLocal() as session:
                # Seed Organization
                org = Organization(name="Test Org", id=1)
                session.add(org)
                # Seed User because get_current_user usually fetches it from DB (although we mocked it)
                # But override_get_current_user returns a detached object.
                # If the API endpoint tries to access user relationships or if we want to be safe, we should add it.
                # But get_current_user override returns the object directly, so it should be fine.
                await session.commit()

            print("Starting verification...")
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # 1. Create Order
                print("1. Testing POST /api/v2/genotyping/vendor/orders")
                payload = {
                    "clientId": "CLIENT-001",
                    "numberOfSamples": 96,
                    "serviceIds": ["GBS", "WGS"]
                }
                response = await ac.post("/api/v2/genotyping/vendor/orders", json=payload)
                print(f"   Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"   Error: {response.text}")
                assert response.status_code == 200
                data = response.json()["result"]
                assert data["clientId"] == "CLIENT-001"
                assert data["status"] == "submitted"
                order_db_id = data["vendorOrderDbId"]
                print(f"   Created Order DB ID: {order_db_id}")

                # 2. Get Order
                print(f"2. Testing GET /api/v2/genotyping/vendor/orders/{order_db_id}")
                response = await ac.get(f"/api/v2/genotyping/vendor/orders/{order_db_id}")
                assert response.status_code == 200
                data = response.json()["result"]
                assert data["vendorOrderDbId"] == order_db_id
                print("   Success")

                # 3. List Orders
                print("3. Testing GET /api/v2/genotyping/vendor/orders")
                response = await ac.get("/api/v2/genotyping/vendor/orders")
                assert response.status_code == 200
                data = response.json()["result"]["data"]
                assert len(data) >= 1
                print(f"   Found {len(data)} orders")

                # 4. Update Status
                print(f"4. Testing PUT /api/v2/genotyping/vendor/orders/{order_db_id}/status")
                payload = {"status": "in_progress"}
                response = await ac.put(f"/api/v2/genotyping/vendor/orders/{order_db_id}/status", json=payload)
                assert response.status_code == 200
                data = response.json()["result"]
                assert data["status"] == "in_progress"
                print("   Status updated to 'in_progress'")

            print("\nVerification Successful!")

        if __name__ == "__main__":
            try:
                asyncio.run(verify())
            except Exception as e:
                print(f"Verification Failed: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
