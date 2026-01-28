"""
GAIA API Server — FastAPI endpoint for the Geospatial Agent.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import agent
from langchain_core.messages import HumanMessage
import uvicorn

app = FastAPI(title="GAIA API", description="Geospatial Intelligence Agent for Bijmantra")

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
    return {"status": "running", "agent": "GAIA", "domain": "Geospatial Intelligence"}


class AnalyzeRequest(BaseModel):
    query: str


class AnalyzeResponse(BaseModel):
    response: str


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    """
    Analyze a geospatial query using the GAIA agent.
    Example: "Find drought-prone trial sites in Gujarat"
    """
    print(f"GAIA API Request: {request.query}")
    try:
        final_answer = ""

        async for chunk in agent.astream({"messages": [HumanMessage(content=request.query)]}, stream_mode="values"):
            last_msg = chunk["messages"][-1]

            if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
                final_answer = last_msg.content

        if not final_answer:
            final_answer = "GAIA processed your request but could not formulate a response."

        return AnalyzeResponse(response=final_answer)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=8082, reload=True)
