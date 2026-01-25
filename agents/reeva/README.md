# REEVA Agent

This folder contains the standalone AI agent for Bijmantra.

## Setup

1. Create virtual environment: `python3 -m venv .venv`
2. Install tools: `pip install -r requirements.txt`
3. Run Server: `uvicorn src.server:app --port 8081`

## Structure

- `src/agent.py`: LangGraph logic
- `src/server.py`: FastAPI endpoint
