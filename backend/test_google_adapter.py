import asyncio
import os
import httpx
from app.modules.ai.adapters.google_adapter import GoogleAdapter
from app.modules.ai.services.provider_types import LLMConfig, LLMProvider

async def main():
    async def get_client():
        return httpx.AsyncClient()

    adapter = GoogleAdapter(get_client)
    
    config = LLMConfig(
        provider=LLMProvider.GOOGLE,
        model="gemini bad model", # Bad model name with spaces
        api_key=os.getenv("GOOGLE_AI_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta",
        max_tokens=100,
        temperature=0.7,
        available=True,
    )
    
    messages = [{"role": "user", "content": "Hello!"}]
    
    try:
        result = await adapter.call(messages, config)
        print("Success:", result.content if result else None)
    except Exception as e:
        print("Caught Exception in adapter.call:", e)

if __name__ == "__main__":
    asyncio.run(main())
