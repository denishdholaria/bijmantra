"""
KENSHA Agent — Vision Intelligence using LangGraph + Gemini Vision.
"""
import os
import asyncio
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools import tools

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """You are KENSHA, the Computer Vision Agent for Bijmantra.
Named after the Japanese concept of "Seer" or "Inspection", your role is to "see" for the breeder — analyzing images of crops, seeds, and fields used in plant breeding.

You have access to tools for:
- Identifying plant diseases from leaf images
- Counting seeds or fruits
- Estimating phenotypic traits

When analyzing:
1. Be precise about visual symptoms.
2. If the image is unclear, ask for a better photo.
3. Provide agronomic context for your observations.

If a user asks about SQL databases or Satellite maps, refer them to REEVA or GAIA respectively.
"""

# Using Gemini 1.5 Flash (Multimodal)
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

async def main():
    # Simple CLI test
    if len(sys.argv) < 2:
        print("Usage: python -m src.agent 'Analyze this image: /path/to/leaf.jpg'")
        sys.exit(1)

    user_query = sys.argv[1]
    print(f"KENSHA (Vision): Processing '{user_query}'...")

    async for chunk in agent.astream({"messages": [HumanMessage(content=user_query)]}, stream_mode="values"):
        last_msg = chunk["messages"][-1]
        if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
            print("\n---------------------------------------------------")
            print("KENSHA Response:")
            print(last_msg.content)
            print("---------------------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
