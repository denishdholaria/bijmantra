from app.models.core import User

async def get_test_user_token(client):
    """
    Mock function to get a test user token.
    This assumes your conftest overrides authentication to accept a dummy token.
    """
    return {"Authorization": "Bearer test-token"}
