"""
VEENA Omega API Server — The Central Hub.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.graph import orchestrator_app
from langchain_core.messages import HumanMessage
import uvicorn

app = FastAPI(title="VEENA Omega API", description="Central Orchestrator for Agent Arsenal")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "status": "running",
        "agent": "VEENA Omega",
        "role": "Orchestrator",
        "connected_agents": ["REEVA", "GAIA", "KENSHA"]
    }

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    agent_used: str = "Unknown"

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint. Receives query, routes to appropriate agent, returns answer.
    """
    print(f"VEENA Request: {request.query}")
    try:
        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=request.query)],
            "next_agent": "",
            "final_response": ""
        }
        
        # Run graph
        result = await orchestrator_app.ainvoke(initial_state)
        
        return ChatResponse(
            response=result.get("final_response", "No response generated."),
            agent_used=result.get("next_agent", "General")
        )

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=8080, reload=True)
