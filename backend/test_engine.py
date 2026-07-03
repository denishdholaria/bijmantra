import asyncio
import os
from app.modules.ai.services.engine import MultiTierLLMService
from app.modules.ai.services.provider_types import LLMProvider

async def main():
    engine = MultiTierLLMService()
    
    try:
        response = await engine.chat(
            user_message="Hello!",
            preferred_provider=LLMProvider.GOOGLE,
            user_api_key=os.getenv("GOOGLE_AI_KEY"),
            user_model="gemini bad model test"
        )
        print("Response Content:", response.content)
    except Exception as e:
        print("Caught Exception in engine:", e)

if __name__ == "__main__":
    asyncio.run(main())
