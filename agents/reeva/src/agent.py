import os
import asyncio
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from src.tools import list_tables_tool, get_table_schema_tool, run_query_tool

# Load environment variables
load_dotenv()

# Initialize Model
# Using Gemini Flash for stability and speed
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Define Tools
tools = [list_tables_tool, get_table_schema_tool, run_query_tool]

# Create Agent
agent = create_react_agent(llm, tools)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python src/agent.py 'Your query here'")
        sys.exit(1)

    user_query = sys.argv[1]
    print(f"REEVA (Python): Processing query '{user_query}'...")

    async for chunk in agent.astream({"messages": [HumanMessage(content=user_query)]}, stream_mode="values"):
        last_msg = chunk["messages"][-1]
        
        # If it's an AI message and has content (final answer), print it
        if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
            print("\n---------------------------------------------------")
            print("REEVA Response:")
            print(last_msg.content)
            print("---------------------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
