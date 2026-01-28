"""
VEENA Omega — The Orchestrator Graph.
Uses LangGraph to route queries to specialized agents.
"""
import os
import httpx
from typing import TypedDict, List, Annotated
import operator
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END

load_dotenv()

# --- Configuration ---
AGENTS = {
    "REEVA": "http://bijmantra-reeva:8081/api/chat",
    "GAIA": "http://bijmantra-gaia:8082/api/analyze",
    "KENSHA": "http://bijmantra-kensha:8083/api/analyze-text",
}

# --- State Definition ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    next_agent: str
    final_response: str


# --- Tool / Node Definitions ---

async def router_node(state: AgentState):
    """
    Decides which agent to call based on the user's last message.
    """
    # Initialize LLM for routing
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    last_message = state["messages"][-1].content
    
    # Simple classification prompt
    system_msg = """You are the Router for the Bijmantra Agricultural AI.
    Classify the user's query into one of these categories:
    - DATABSE: Questions about trials, tables, sql, specific data records. (Agent: REEVA)
    - GEOSPATIAL: Questions about maps, locations, satellite data, weather, NDVI, suitability. (Agent: GAIA)
    - VISION: Questions about analyzing images, plant diseases, phenotyping, visual traits. (Agent: KENSHA)
    - GENERAL: General chat, greetings, or questions not fitting above. (Handle locally)
    
    Output ONLY the category name.
    """
    
    response = await llm.ainvoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=last_message)
    ])
    
    intent = response.content.strip().upper()
    print(f"Router Decision: {intent}")
    
    if "DATABSE" in intent or "REEVA" in intent:
        return {"next_agent": "REEVA"}
    elif "GEOSPATIAL" in intent or "GAIA" in intent:
        return {"next_agent": "GAIA"}
    elif "VISION" in intent or "KENSHA" in intent:
        return {"next_agent": "KENSHA"}
    else:
        return {"next_agent": "GENERAL"}


async def call_reeva(state: AgentState):
    query = state["messages"][-1].content
    print(f"Calling REEVA with: {query}")
    try:
        async with httpx.AsyncClient() as client:
            # Note: In docker-compose, hostname 'bijmantra-reeva' works.
            # Local fallback for testing: localhost:8081
            url = AGENTS["REEVA"]
            if os.getenv("LOCAL_TEST"): url = "http://localhost:8081/api/chat"
            
            resp = await client.post(url, json={"query": query}, timeout=30.0)
            result = resp.json().get("response", "Error from REEVA")
            return {"final_response": f"**REEVA (Data Agent):**\n{result}"}
            
    except Exception as e:
        return {"final_response": f"Failed to contact REEVA: {str(e)}"}


async def call_gaia(state: AgentState):
    query = state["messages"][-1].content
    print(f"Calling GAIA with: {query}")
    try:
        async with httpx.AsyncClient() as client:
            url = AGENTS["GAIA"]
            if os.getenv("LOCAL_TEST"): url = "http://localhost:8082/api/analyze"
            
            resp = await client.post(url, json={"query": query}, timeout=30.0)
            result = resp.json().get("response", "Error from GAIA")
            return {"final_response": f"**GAIA (Geospatial Agent):**\n{result}"}
            
    except Exception as e:
        return {"final_response": f"Failed to contact GAIA: {str(e)}"}


async def call_kensha(state: AgentState):
    query = state["messages"][-1].content
    print(f"Calling KENSHA with: {query}")
    try:
        async with httpx.AsyncClient() as client:
            url = AGENTS["KENSHA"]
            if os.getenv("LOCAL_TEST"): url = "http://localhost:8083/api/analyze-text"
            
            resp = await client.post(url, json={"query": query}, timeout=30.0)
            result = resp.json().get("response", "Error from KENSHA")
            # In a real scenario, we might also pass a file URL if provided
            return {"final_response": f"**KENSHA (Vision Agent):**\n{result}"}
            
    except Exception as e:
         return {"final_response": f"Failed to contact KENSHA: {str(e)}"}


async def general_response(state: AgentState):
    """Handle general queries directly."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        temperature=0.7,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    msg = state["messages"][-1].content
    resp = await llm.ainvoke([
        SystemMessage(content="You are VEENA, the intelligent assistant for Bijmantra. Answer helpfully."),
        HumanMessage(content=msg)
    ])
    return {"final_response": resp.content}


# --- Graph Construction ---

workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("reeva_node", call_reeva)
workflow.add_node("gaia_node", call_gaia)
workflow.add_node("kensha_node", call_kensha)
workflow.add_node("general_node", general_response)

workflow.set_entry_point("router")

def route_condition(state: AgentState):
    return state["next_agent"]

workflow.add_conditional_edges(
    "router",
    route_condition,
    {
        "REEVA": "reeva_node",
        "GAIA": "gaia_node",
        "KENSHA": "kensha_node",
        "GENERAL": "general_node"
    }
)

workflow.add_edge("reeva_node", END)
workflow.add_edge("gaia_node", END)
workflow.add_edge("kensha_node", END)
workflow.add_edge("general_node", END)

orchestrator_app = workflow.compile()
