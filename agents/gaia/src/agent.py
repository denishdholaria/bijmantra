"""
GAIA Agent — Geospatial Intelligence using LangGraph + Gemini.
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

# System prompt for geospatial reasoning
SYSTEM_PROMPT = """You are GAIA, the Geospatial Intelligence Agent for Bijmantra.
Named after the Greek goddess of Earth, you bridge satellite data with agricultural breeding decisions.

You have access to tools for:
- Calculating vegetation indices (NDVI) from satellite imagery
- Finding suitable trial sites based on environmental criteria
- Analyzing the environmental profile of existing trial locations

When answering questions:
1. Use the appropriate geospatial tool to gather data.
2. Interpret the results in the context of plant breeding.
3. Provide actionable recommendations based on satellite observations.

Remember: You are one agent in a larger system. If a question is not about geospatial analysis, 
politely indicate that another agent (like REEVA for database queries) may be more appropriate.
"""

# Initialize Gemini Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Create the ReAct agent
agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.agent 'Your geospatial query here'")
        sys.exit(1)

    user_query = sys.argv[1]
    print(f"GAIA (Geospatial): Processing query '{user_query}'...")

    async for chunk in agent.astream({"messages": [HumanMessage(content=user_query)]}, stream_mode="values"):
        last_msg = chunk["messages"][-1]

        # If it's an AI message and has content (final answer), print it
        if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
            print("\n---------------------------------------------------")
            print("GAIA Response:")
            print(last_msg.content)
            print("---------------------------------------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
