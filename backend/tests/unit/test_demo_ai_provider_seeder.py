from app.db.seeders.demo_ai_provider import DemoAIProviderSeeder
from app.models.ai_configuration import AIProvider, AIProviderModel
from app.models.base import Base
from app.models.core import Organization


def test_demo_ai_provider_seeder_clones_admin_ollama_provider_without_secrets(db_session):
    Base.metadata.create_all(
        bind=db_session.bind,
        tables=[
            Base.metadata.tables[name]
            for name in ("organizations", "ai_providers", "ai_provider_models")
            if name in Base.metadata.tables
        ],
    )

    admin_org = Organization(
        id=1,
        name="BijMantra HQ",
        contact_email="admin@bijmantra.org",
        is_active=True,
    )
    demo_org = Organization(
        id=2,
        name="Demo Organization",
        contact_email="demo@bijmantra.org",
        is_active=True,
    )
    db_session.add_all([admin_org, demo_org])
    db_session.flush()

    admin_provider = AIProvider(
        organization_id=admin_org.id,
        provider_key="ollama",
        display_name="Ollama Local",
        base_url="http://localhost:11434",
        auth_mode="api_key",
        encrypted_api_key="admin-local-secret",
        priority=70,
        is_enabled=True,
        is_byok_allowed=True,
    )
    db_session.add(admin_provider)
    db_session.flush()
    db_session.add(
        AIProviderModel(
            organization_id=admin_org.id,
            provider_id=admin_provider.id,
            model_name="lfm2.5-thinking:latest",
            display_name="LFM2.5 Thinking",
            is_default=True,
            is_active=True,
            is_streaming_supported=True,
        )
    )
    db_session.commit()

    assert DemoAIProviderSeeder(db_session).seed() == 2

    demo_provider = (
        db_session.query(AIProvider)
        .filter(
            AIProvider.organization_id == demo_org.id,
            AIProvider.provider_key == "ollama",
        )
        .one()
    )
    assert demo_provider.base_url == "http://localhost:11434"
    assert demo_provider.encrypted_api_key is None
    assert demo_provider.is_enabled is True

    demo_model = (
        db_session.query(AIProviderModel)
        .filter(
            AIProviderModel.organization_id == demo_org.id,
            AIProviderModel.provider_id == demo_provider.id,
        )
        .one()
    )
    assert demo_model.model_name == "lfm2.5-thinking:latest"
    assert demo_model.is_default is True

    assert DemoAIProviderSeeder(db_session).seed() == 0
