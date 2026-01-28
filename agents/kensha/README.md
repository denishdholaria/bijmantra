# CHAKSHU Agent — Computer Vision Intelligence

> **चक्षु** (Chakshu) = Eye
> This agent sees what the breeder sees.

## Purpose

- Analyze crop images for disease detection
- Perform digital phenotyping (counting, measuring)
- Integrate with MinIO for image storage and retrieval

## Future Vision: VL-JEPA

> "Intelligence = World Modeling, Not Word Prediction"

This agent currently uses **Gemini 1.5 Flash** for immediate visual reasoning (Short Term Strategy).
In the long term, CHAKSHU will evolve to use **VL-JEPA** (Vision-Language Joint Embedding Predictive Architecture) to model crop growth states temporally, moving beyond simple classification to causal prediction (e.g., _Stress emergence_ vs _Visual symptom_).

Reference: `docs/gupt/7-VL-JEPA.md`

## Setup

```bash
cd chakshu
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn src.server:app --port 8083
```

## API Endpoints

- `POST /api/analyze-image` — Analyze an uploaded image or MinIO URL
