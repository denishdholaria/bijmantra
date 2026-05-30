"""
Pipeline Dataset API
Read-only endpoints for the demo datasets loaded from /Volumes/S1/dataset.

Endpoints:
  GET /api/v2/data/pipeline/crop-yields
  GET /api/v2/data/pipeline/crop-recommendation
  GET /api/v2/data/pipeline/fertilizer
  GET /api/v2/data/pipeline/india-production
  GET /api/v2/data/pipeline/weather
  GET /api/v2/data/pipeline/summary
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.deps import get_db

router = APIRouter(prefix="/pipeline", tags=["Pipeline Datasets"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _paginate(page: int, page_size: int) -> tuple[int, int]:
    page_size = min(page_size, 500)
    offset = (page - 1) * page_size
    return page_size, offset


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/summary")
async def get_pipeline_summary(db: AsyncSession = Depends(get_db)):
    """Row counts and metadata for all loaded pipeline datasets."""
    tables = {
        "crop_yields":           "pipeline_crop_yields",
        "crop_recommendation":   "pipeline_crop_recommendation",
        "fertilizer_prediction": "pipeline_fertilizer_prediction",
        "india_crop_production": "pipeline_india_crop_production",
        "delhi_climate":         "pipeline_delhi_climate",
        "weather_observations":  "pipeline_weather_observations",
    }
    summary = {}
    for key, table in tables.items():
        try:
            n = (await db.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
            summary[key] = {"table": table, "rows": n, "status": "loaded"}
        except Exception:
            summary[key] = {"table": table, "rows": 0, "status": "not_found"}

    return {
        "datasets": summary,
        "total_rows": sum(v["rows"] for v in summary.values()),
        "source": "/Volumes/S1/dataset",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Crop Yields  (Kaggle: patelris/crop-yield-prediction-dataset)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/crop-yields")
async def get_crop_yields(
    country: Optional[str] = Query(None, description="Filter by country name"),
    crop:    Optional[str] = Query(None, description="Filter by crop name"),
    year:    Optional[int] = Query(None, description="Filter by year"),
    page:    int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Global crop yield data with rainfall, pesticide use, and temperature.
    Source: Kaggle patelris/crop-yield-prediction-dataset (~13k rows).
    """
    limit, offset = _paginate(page, page_size)

    where, params = [], {}
    if country:
        where.append("LOWER(country) LIKE :country")
        params["country"] = f"%{country.lower()}%"
    if crop:
        where.append("LOWER(crop) LIKE :crop")
        params["crop"] = f"%{crop.lower()}%"
    if year:
        where.append("year = :year")
        params["year"] = year

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = (await db.execute(
        text(f"SELECT COUNT(*) FROM pipeline_crop_yields {where_sql}"), params
    )).scalar()

    rows = (await db.execute(
        text(f"""
            SELECT country, crop, year, yield_hg_ha,
                   ROUND(yield_hg_ha::numeric / 100, 2) AS yield_t_ha,
                   rainfall_mm, pesticides_t, avg_temp_c
            FROM pipeline_crop_yields {where_sql}
            ORDER BY country, crop, year
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset},
    )).mappings().all()

    return {
        "total": total,
        "page": page,
        "page_size": limit,
        "data": [dict(r) for r in rows],
    }


@router.get("/crop-yields/countries")
async def get_crop_yield_countries(db: AsyncSession = Depends(get_db)):
    """Distinct countries in the crop yield dataset."""
    rows = (await db.execute(
        text("SELECT DISTINCT country FROM pipeline_crop_yields ORDER BY country")
    )).scalars().all()
    return {"countries": rows}


@router.get("/crop-yields/crops")
async def get_crop_yield_crops(db: AsyncSession = Depends(get_db)):
    """Distinct crop names in the crop yield dataset."""
    rows = (await db.execute(
        text("SELECT DISTINCT crop FROM pipeline_crop_yields ORDER BY crop")
    )).scalars().all()
    return {"crops": rows}


# ══════════════════════════════════════════════════════════════════════════════
# Crop Recommendation  (Kaggle: atharvaingle)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/crop-recommendation")
async def get_crop_recommendation(
    crop_label: Optional[str] = Query(None, description="Filter by crop label"),
    page:       int = Query(1, ge=1),
    page_size:  int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Soil + climate conditions mapped to recommended crop.
    Source: Kaggle atharvaingle/crop-recommendation-dataset (~2.2k rows).
    """
    limit, offset = _paginate(page, page_size)

    where, params = [], {}
    if crop_label:
        where.append("LOWER(crop_label) LIKE :crop_label")
        params["crop_label"] = f"%{crop_label.lower()}%"

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = (await db.execute(
        text(f"SELECT COUNT(*) FROM pipeline_crop_recommendation {where_sql}"), params
    )).scalar()

    rows = (await db.execute(
        text(f"""
            SELECT nitrogen, phosphorus, potassium, temperature,
                   humidity, ph, rainfall, crop_label
            FROM pipeline_crop_recommendation {where_sql}
            ORDER BY crop_label
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset},
    )).mappings().all()

    return {
        "total": total,
        "page": page,
        "page_size": limit,
        "data": [dict(r) for r in rows],
    }


@router.get("/crop-recommendation/crops")
async def get_recommendation_crops(db: AsyncSession = Depends(get_db)):
    """Distinct crop labels with counts."""
    rows = (await db.execute(text("""
        SELECT crop_label, COUNT(*) as count
        FROM pipeline_crop_recommendation
        GROUP BY crop_label ORDER BY crop_label
    """))).mappings().all()
    return {"crops": [dict(r) for r in rows]}


# ══════════════════════════════════════════════════════════════════════════════
# Fertilizer Prediction  (Kaggle: gdabhishek)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/fertilizer")
async def get_fertilizer_prediction(
    crop_type:       Optional[str] = Query(None),
    soil_type:       Optional[str] = Query(None),
    fertilizer_name: Optional[str] = Query(None),
    page:     int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Soil conditions → fertilizer recommendation.
    Source: Kaggle gdabhishek/fertilizer-prediction (~99 rows).
    """
    limit, offset = _paginate(page, page_size)

    where, params = [], {}
    if crop_type:
        where.append("LOWER(crop_type) LIKE :crop_type")
        params["crop_type"] = f"%{crop_type.lower()}%"
    if soil_type:
        where.append("LOWER(soil_type) LIKE :soil_type")
        params["soil_type"] = f"%{soil_type.lower()}%"
    if fertilizer_name:
        where.append("LOWER(fertilizer_name) LIKE :fertilizer_name")
        params["fertilizer_name"] = f"%{fertilizer_name.lower()}%"

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = (await db.execute(
        text(f"SELECT COUNT(*) FROM pipeline_fertilizer_prediction {where_sql}"), params
    )).scalar()

    rows = (await db.execute(
        text(f"""
            SELECT temperature, humidity, moisture, soil_type, crop_type,
                   nitrogen, potassium, phosphorous, fertilizer_name
            FROM pipeline_fertilizer_prediction {where_sql}
            ORDER BY crop_type, fertilizer_name
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset},
    )).mappings().all()

    return {
        "total": total,
        "page": page,
        "page_size": limit,
        "data": [dict(r) for r in rows],
    }


# ══════════════════════════════════════════════════════════════════════════════
# India Crop Production  (Kaggle: abhinand05)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/india-production")
async def get_india_crop_production(
    state:    Optional[str] = Query(None, description="Filter by state name"),
    crop:     Optional[str] = Query(None, description="Filter by crop name"),
    season:   Optional[str] = Query(None, description="Filter by season"),
    year:     Optional[int] = Query(None, description="Filter by crop year"),
    page:     int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    India state/district level crop production data.
    Source: Kaggle abhinand05/crop-production-in-india (~246k rows).
    """
    limit, offset = _paginate(page, page_size)

    where, params = [], {}
    if state:
        where.append("LOWER(state_name) LIKE :state")
        params["state"] = f"%{state.lower()}%"
    if crop:
        where.append("LOWER(crop) LIKE :crop")
        params["crop"] = f"%{crop.lower()}%"
    if season:
        where.append("LOWER(season) LIKE :season")
        params["season"] = f"%{season.lower()}%"
    if year:
        where.append("crop_year = :year")
        params["year"] = year

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = (await db.execute(
        text(f"SELECT COUNT(*) FROM pipeline_india_crop_production {where_sql}"), params
    )).scalar()

    rows = (await db.execute(
        text(f"""
            SELECT state_name, district_name, crop_year, season,
                   crop, area_ha, production_t
            FROM pipeline_india_crop_production {where_sql}
            ORDER BY state_name, crop_year DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset},
    )).mappings().all()

    return {
        "total": total,
        "page": page,
        "page_size": limit,
        "data": [dict(r) for r in rows],
    }


@router.get("/india-production/states")
async def get_india_states(db: AsyncSession = Depends(get_db)):
    """Distinct states in the India crop production dataset."""
    rows = (await db.execute(
        text("SELECT DISTINCT state_name FROM pipeline_india_crop_production ORDER BY state_name")
    )).scalars().all()
    return {"states": rows}


# ══════════════════════════════════════════════════════════════════════════════
# Weather Observations  (NASA POWER)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/weather")
async def get_weather_observations(
    country:    Optional[str] = Query(None),
    location:   Optional[str] = Query(None),
    date_from:  Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to:    Optional[str] = Query(None, description="YYYY-MM-DD"),
    page:       int = Query(1, ge=1),
    page_size:  int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Daily weather observations from NASA POWER for 13 global agricultural locations.
    Source: NASA POWER agroclimatology API (~30k rows, 2010–2023).
    """
    limit, offset = _paginate(page, page_size)

    where, params = [], {}
    if country:
        where.append("LOWER(country) LIKE :country")
        params["country"] = f"%{country.lower()}%"
    if location:
        where.append("LOWER(location_name) LIKE :location")
        params["location"] = f"%{location.lower()}%"
    if date_from:
        where.append("obs_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("obs_date <= :date_to")
        params["date_to"] = date_to

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = (await db.execute(
        text(f"SELECT COUNT(*) FROM pipeline_weather_observations {where_sql}"), params
    )).scalar()

    rows = (await db.execute(
        text(f"""
            SELECT location_name, country, region, latitude, longitude,
                   obs_date, temperature_c, precipitation_mm, humidity_pct, wind_speed_ms
            FROM pipeline_weather_observations {where_sql}
            ORDER BY country, obs_date
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": limit, "offset": offset},
    )).mappings().all()

    return {
        "total": total,
        "page": page,
        "page_size": limit,
        "data": [dict(r) for r in rows],
    }


@router.get("/weather/locations")
async def get_weather_locations(db: AsyncSession = Depends(get_db)):
    """All locations available in the weather dataset with date ranges."""
    rows = (await db.execute(text("""
        SELECT location_name, country, region,
               latitude, longitude,
               MIN(obs_date) AS date_from,
               MAX(obs_date) AS date_to,
               COUNT(*) AS days
        FROM pipeline_weather_observations
        GROUP BY location_name, country, region, latitude, longitude
        ORDER BY country, location_name
    """))).mappings().all()
    return {"locations": [dict(r) for r in rows]}
