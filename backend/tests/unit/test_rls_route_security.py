from fastapi.params import Depends

from app.api.bijmantra.security.rls import router
from app.api.deps import get_current_superuser


def test_rls_router_requires_superuser_dependency():
    dependencies = [dependency.dependency for dependency in router.dependencies]

    assert get_current_superuser in dependencies
    assert all(isinstance(dependency, Depends) for dependency in router.dependencies)
