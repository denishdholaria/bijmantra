from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import agent
from langchain_core.messages import HumanMessage
import uvicorn
import os

app = FastAPI(title="REEVA API", description="Backend API for REEVA AI Agent")

# Allow CORS for development (Frontend usually runs on 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "running", "message": "REEVA API is active. Use POST /api/chat to interact."}

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    tool_calls: list = []

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"API Request: {request.query}")
    try:
        final_answer = ""
        tool_logs = []
        
        # Stream the agent's execution to capture thoughts and final answer
        async for chunk in agent.astream({"messages": [HumanMessage(content=request.query)]}, stream_mode="values"):
            last_msg = chunk["messages"][-1]
            
            # Capture tool usage (if any)
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                tool_logs.extend(last_msg.tool_calls)

            # Capture final answer
            if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
                final_answer = last_msg.content

        if not final_answer:
            # Fallback if no clean final answer found (rare)
            final_answer = "I processed your request but had trouble formulating a final answer. Please check the logs."

        return ChatResponse(response=final_answer, tool_calls=tool_logs)

    except Exception as e:
        print(f"Error: {e}")
        # In case of API limits or other crashes, return the error
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=8081, reload=True)
