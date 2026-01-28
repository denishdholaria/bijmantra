# GAIA Agent — Geospatial Intelligence

> **GAIA** = Greek goddess of Earth
> This agent connects satellite data with breeding decisions.

## Purpose

- Analyze trial site suitability using satellite imagery
- Calculate vegetation indices (NDWI, NDVI)
- Integrate with Google Earth Engine for environmental queries

## Setup

```bash
cd gaia
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn src.server:app --port 8082
```

## API Endpoints

- `POST /api/analyze` — Analyze a location for trial suitability
- `POST /api/ndvi` — Get NDVI time series for coordinates
