import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.veena_cognitive import ReasoningTrace, UserContext, VeenaAuditLog, VeenaMemory
from app.services.veena_cognitive_service import VeenaCognitiveService


@pytest.fixture
async def cognitive_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            VeenaMemory.__table__,
            ReasoningTrace.__table__,
            UserContext.__table__,
            VeenaAuditLog.__table__,
        ])

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_store_memory_and_retrieve_context(cognitive_session):
    service = VeenaCognitiveService(cognitive_session)

    await service.store_memory(1, {"query": "best drought cross", "response": "Use line A x line B", "context_tags": ["drought"]})
    await service.store_memory(1, {"query": "rice maturity", "response": "~110 days", "context_tags": ["maturity"]})
    await cognitive_session.commit()

    records = await service.retrieve_relevant_context(1, "drought tolerant cross", limit=2)
    assert len(records) == 2
    assert records[0].user_id == 1


@pytest.mark.asyncio
async def test_log_reasoning_step(cognitive_session):
    service = VeenaCognitiveService(cognitive_session)

    trace = await service.log_reasoning_step(
        "session-1",
        {
            "step_id": "step-1",
            "thought": "Need nearest parent with drought tolerance",
            "tool_used": "vector-search",
            "outcome": "candidate-shortlist",
        },
    )
    await cognitive_session.commit()

    assert trace.id is not None
    assert trace.session_id == "session-1"
    assert trace.outcome == "candidate-shortlist"
