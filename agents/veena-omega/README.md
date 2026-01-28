# VEENA Omega — The Orchestrator

> **वीणा** (Veena) = Instrument of Wisdom
> The central brain that coordinates the 1,000-armed Agent Arsenal (SAHASRABHUJA).

## Purpose

- Receive user queries from the frontend.
- **Classify Intent**: Decide which specialist agent(s) to call.
- **Route**: Dispatch requests to REEVA, GAIA, or CHAKSHU.
- **Synthesize**: Combine results into a single answer.

## Architecture

- **Port**: 8080
- **Framework**: LangGraph + FastAPI
- **Model**: Gemini Flash (Latest)

## Agents Mapped

- `REEVA` (Data) -> `http://bijmantra-reeva:8081/api/chat`
- `GAIA` (Geospatial) -> `http://bijmantra-gaia:8082/api/analyze`
- `CHAKSHU` (Vision) -> `http://bijmantra-chakshu:8083/api/analyze-text`

## Setup

```bash
cd veena-omega
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn src.server:app --port 8080
```
