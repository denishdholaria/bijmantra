"""
KENSHA API Server — FastAPI endpoint for the Vision Agent.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import agent
from langchain_core.messages import HumanMessage
import uvicorn
import shutil
import os

app = FastAPI(title="KENSHA API", description="Computer Vision Agent for Bijmantra")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/kensha_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "running", "agent": "KENSHA", "domain": "Computer Vision"}

class VisionRequest(BaseModel):
    query: str
    image_url: str = None  # Optional URL handling

class VisionResponse(BaseModel):
    response: str

@app.post("/api/analyze-text", response_model=VisionResponse)
async def analyze_text(request: VisionRequest):
    """
    Standard text-based chat about vision (e.g. "What features can you see?").
    """
    try:
        final_answer = ""
        async for chunk in agent.astream({"messages": [HumanMessage(content=request.query)]}, stream_mode="values"):
            last_msg = chunk["messages"][-1]
            if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
                final_answer = last_msg.content
        
        if not final_answer:
            final_answer = "KENSHA processed request but gave no output."
            
        return VisionResponse(response=final_answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-analyze")
async def upload_analyze(file: UploadFile = File(...), query: str = "Analyze this image"):
    """
    Upload an image file and analyze it. 
    Notes: In a real system, we'd stream this to MinIO/S3. Here we save to tmp.
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Construct a query that points the agent to the file path
        # The agent's tools (in tools.py) would theoretically pick this up.
        full_query = f"{query}. Image path: {file_path}"
        
        final_answer = ""
        async for chunk in agent.astream({"messages": [HumanMessage(content=full_query)]}, stream_mode="values"):
            last_msg = chunk["messages"][-1]
            if last_msg.type == "ai" and last_msg.content and not last_msg.tool_calls:
                final_answer = last_msg.content
                
        return {"filename": file.filename, "analysis": final_answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=8083, reload=True)
