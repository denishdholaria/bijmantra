#!/usr/bin/env python3
"""
Demo Dataset Loader — loads all downloaded datasets from /Volumes/S1/dataset
into the BijMantra PostgreSQL database for testing.

Datasets loaded:
  1. Kaggle: Crop Yield Prediction (28,242 records)
  2. Kaggle: Crop Recommendation (2,200 records)
  3. Kaggle: Fertilizer Prediction (99 records)
  4. Kaggle: Indian Crop Production (246,091 records)
  5. Kaggle: Daily Delhi Climate (114 records)
  6. NASA POWER: Weather observations (17 locations, ~68k records)

Usage:
    cd backend
    uv run python scripts/load_demo_datasets.py
    uv run python scripts/load_demo_datasets.py --force   # re-seed even if data exists
    uv run python scripts/load_demo_datasets.py --only=yields,weather
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ── Paths ──────────────────────────────────────────────────────────────────────
DATASET_ROOT = Path("/Volumes/S1/dataset")
KAGGLE_CACHE = DATASET_ROOT / "kaggle" / ".kagglehub-cache" / "datasets"
NASA_POWER_DIR = DATASET_ROOT / "nasa-power"
USDA_NASS_DIR = DATASET_ROOT / "usda-nass"

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── DB helpers ─────────────────────────────────────────────────────────────────

def get_session() -> Session:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.core.config import settings
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
    return sessionmaker(bind=engine)()


def table_count(db: Session, table: str) -> int:
    """Return row count for table, or -1 if table doesn't exist."""
    try:
        exists = db.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=:t)"
        ), {"t": table}).scalar()
        if not exists:
            return -1
        return db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    except Exception:
        db.rollback()
        return -1


def bulk_insert(db: Session, sql: str, rows: list[dict], batch: int = 500) -> int:
    inserted = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        result = db.execute(text(sql), chunk)
        inserted += result.rowcount
    return inserted


# ══════════════════════════════════════════════════════════════════════════════
# 1. Crop Yield Prediction (patelris/crop-yield-prediction-dataset)
# ══════════════════════════════════════════════════════════════════════════════

def load_crop_yields(db: Session, force: bool = False) -> int:
    """
    Loads yield_df.csv — global crop yield data with rainfall, pesticides, temp.
    Columns: Area, Item, Year, hg/ha_yield, average_rain_fall_mm_per_year,
             pesticides_tonnes, avg_temp
    """
    table = "pipeline_crop_yields"
    existing = table_count(db, table)
    if existing > 0 and not force:
        log.info(f"  ↳ {table}: {existing:,} rows already present, skipping (use --force to reload)")
        return 0

    csv_path = (
        KAGGLE_CACHE
        / "patelris"
        / "crop-yield-prediction-dataset"
        / "versions"
        / "4"
        / "yield_df.csv"
    )
    if not csv_path.exists():
        log.warning(f"  ✗ File not found: {csv_path}")
        return 0

    db.rollback()
    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.execute(text(f"""
        CREATE TABLE {table} (
            id              SERIAL PRIMARY KEY,
            country         VARCHAR(100) NOT NULL,
            crop            VARCHAR(100) NOT NULL,
            year            INTEGER      NOT NULL,
            yield_hg_ha     FLOAT,
            rainfall_mm     FLOAT,
            pesticides_t    FLOAT,
            avg_temp_c      FLOAT,
            source          VARCHAR(50)  DEFAULT 'kaggle_patelris',
            created_at      TIMESTAMPTZ  DEFAULT NOW(),
            UNIQUE (country, crop, year, source)
        )
    """))
    db.execute(text(f"CREATE INDEX ON {table} (country)"))
    db.execute(text(f"CREATE INDEX ON {table} (crop)"))
    db.execute(text(f"CREATE INDEX ON {table} (year)"))
    db.commit()

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                rows.append({
                    "country":      row.get("Area", "").strip(),
                    "crop":         row.get("Item", "").strip(),
                    "year":         int(row["Year"]),
                    "yield_hg_ha":  float(row["hg/ha_yield"]) if row.get("hg/ha_yield") else None,
                    "rainfall_mm":  float(row["average_rain_fall_mm_per_year"]) if row.get("average_rain_fall_mm_per_year") else None,
                    "pesticides_t": float(row["pesticides_tonnes"]) if row.get("pesticides_tonnes") else None,
                    "avg_temp_c":   float(row["avg_temp"]) if row.get("avg_temp") else None,
                })
            except (ValueError, KeyError):
                continue

    sql = """
        INSERT INTO pipeline_crop_yields
            (country, crop, year, yield_hg_ha, rainfall_mm, pesticides_t, avg_temp_c, source)
        VALUES
            (:country, :crop, :year, :yield_hg_ha, :rainfall_mm, :pesticides_t, :avg_temp_c, 'kaggle_patelris')
        ON CONFLICT (country, crop, year, source) DO NOTHING
    """
    n = bulk_insert(db, sql, rows)
    log.info(f"  ✓ {table}: inserted {n:,} / {len(rows):,} rows")
    return n


# ══════════════════════════════════════════════════════════════════════════════
# 2. Crop Recommendation (atharvaingle/crop-recommendation-dataset)
# ══════════════════════════════════════════════════════════════════════════════

def load_crop_recommendation(db: Session, force: bool = False) -> int:
    """
    Loads Crop_recommendation.csv — soil/climate → crop label.
    Columns: N, P, K, temperature, humidity, ph, rainfall, label
    """
    table = "pipeline_crop_recommendation"
    existing = table_count(db, table)
    if existing > 0 and not force:
        log.info(f"  ↳ {table}: {existing:,} rows already present, skipping")
        return 0

    csv_path = (
        KAGGLE_CACHE
        / "atharvaingle"
        / "crop-recommendation-dataset"
        / "versions"
        / "1"
        / "Crop_recommendation.csv"
    )
    if not csv_path.exists():
        log.warning(f"  ✗ File not found: {csv_path}")
        return 0

    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.execute(text(f"""
        CREATE TABLE {table} (
            id          SERIAL PRIMARY KEY,
            nitrogen    FLOAT,
            phosphorus  FLOAT,
            potassium   FLOAT,
            temperature FLOAT,
            humidity    FLOAT,
            ph          FLOAT,
            rainfall    FLOAT,
            crop_label  VARCHAR(50),
            source      VARCHAR(50) DEFAULT 'kaggle_atharvaingle',
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    db.execute(text(f"CREATE INDEX ON {table} (crop_label)"))
    db.commit()

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                rows.append({
                    "nitrogen":    float(row["N"]),
                    "phosphorus":  float(row["P"]),
                    "potassium":   float(row["K"]),
                    "temperature": float(row["temperature"]),
                    "humidity":    float(row["humidity"]),
                    "ph":          float(row["ph"]),
                    "rainfall":    float(row["rainfall"]),
                    "crop_label":  row["label"].strip(),
                })
            except (ValueError, KeyError):
                continue

    sql = """
        INSERT INTO pipeline_crop_recommendation
            (nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, crop_label)
        VALUES
            (:nitrogen, :phosphorus, :potassium, :temperature, :humidity, :ph, :rainfall, :crop_label)
    """
    n = bulk_insert(db, sql, rows)
    log.info(f"  ✓ {table}: inserted {n:,} / {len(rows):,} rows")
    return n


# ══════════════════════════════════════════════════════════════════════════════
# 3. Fertilizer Prediction (gdabhishek/fertilizer-prediction)
# ══════════════════════════════════════════════════════════════════════════════

def load_fertilizer_prediction(db: Session, force: bool = False) -> int:
    """
    Loads Fertilizer Prediction.csv — soil conditions → fertilizer name.
    Columns: Temparature, Humidity, Moisture, Soil Type, Crop Type,
             Nitrogen, Potassium, Phosphorous, Fertilizer Name
    """
    table = "pipeline_fertilizer_prediction"
    existing = table_count(db, table)
    if existing > 0 and not force:
        log.info(f"  ↳ {table}: {existing:,} rows already present, skipping")
        return 0

    csv_path = (
        KAGGLE_CACHE
        / "gdabhishek"
        / "fertilizer-prediction"
        / "versions"
        / "1"
        / "Fertilizer Prediction.csv"
    )
    if not csv_path.exists():
        log.warning(f"  ✗ File not found: {csv_path}")
        return 0

    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.execute(text(f"""
        CREATE TABLE {table} (
            id              SERIAL PRIMARY KEY,
            temperature     FLOAT,
            humidity        FLOAT,
            moisture        FLOAT,
            soil_type       VARCHAR(50),
            crop_type       VARCHAR(50),
            nitrogen        FLOAT,
            potassium       FLOAT,
            phosphorous     FLOAT,
            fertilizer_name VARCHAR(100),
            source          VARCHAR(50) DEFAULT 'kaggle_gdabhishek',
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    db.execute(text(f"CREATE INDEX ON {table} (fertilizer_name)"))
    db.execute(text(f"CREATE INDEX ON {table} (crop_type)"))
    db.commit()

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                rows.append({
                    "temperature":     float(row["Temparature"]),
                    "humidity":        float(row["Humidity "]),   # note trailing space
                    "moisture":        float(row["Moisture"]),
                    "soil_type":       row["Soil Type"].strip(),
                    "crop_type":       row["Crop Type"].strip(),
                    "nitrogen":        float(row["Nitrogen"]),
                    "potassium":       float(row["Potassium"]),
                    "phosphorous":     float(row["Phosphorous"]),
                    "fertilizer_name": row["Fertilizer Name"].strip(),
                })
            except (ValueError, KeyError):
                continue

    sql = """
        INSERT INTO pipeline_fertilizer_prediction
            (temperature, humidity, moisture, soil_type, crop_type,
             nitrogen, potassium, phosphorous, fertilizer_name)
        VALUES
            (:temperature, :humidity, :moisture, :soil_type, :crop_type,
             :nitrogen, :potassium, :phosphorous, :fertilizer_name)
    """
    n = bulk_insert(db, sql, rows)
    log.info(f"  ✓ {table}: inserted {n:,} / {len(rows):,} rows")
    return n


# ══════════════════════════════════════════════════════════════════════════════
# 4. Indian Crop Production (abhinand05/crop-production-in-india)
# ══════════════════════════════════════════════════════════════════════════════

def load_india_crop_production(db: Session, force: bool = False) -> int:
    """
    Loads crop_production.csv — India state/district level crop production.
    Columns: State_Name, District_Name, Crop_Year, Season, Crop, Area, Production
    """
    table = "pipeline_india_crop_production"
    existing = table_count(db, table)
    if existing > 0 and not force:
        log.info(f"  ↳ {table}: {existing:,} rows already present, skipping")
        return 0

    csv_path = (
        KAGGLE_CACHE
        / "abhinand05"
        / "crop-production-in-india"
        / "versions"
        / "1"
        / "crop_production.csv"
    )
    if not csv_path.exists():
        log.warning(f"  ✗ File not found: {csv_path}")
        return 0

    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.execute(text(f"""
        CREATE TABLE {table} (
            id            SERIAL PRIMARY KEY,
            state_name    VARCHAR(100),
            district_name VARCHAR(100),
            crop_year     INTEGER,
            season        VARCHAR(50),
            crop          VARCHAR(100),
            area_ha       FLOAT,
            production_t  FLOAT,
            source        VARCHAR(50) DEFAULT 'kaggle_abhinand05',
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    db.execute(text(f"CREATE INDEX ON {table} (state_name)"))
    db.execute(text(f"CREATE INDEX ON {table} (crop)"))
    db.execute(text(f"CREATE INDEX ON {table} (crop_year)"))
    db.commit()

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                area = float(row["Area"]) if row.get("Area") and row["Area"].strip() else None
                prod = float(row["Production"]) if row.get("Production") and row["Production"].strip() else None
                year_str = row.get("Crop_Year", "").strip()
                year = int(year_str) if year_str else None
                rows.append({
                    "state_name":    row.get("State_Name", "").strip(),
                    "district_name": row.get("District_Name", "").strip(),
                    "crop_year":     year,
                    "season":        row.get("Season", "").strip(),
                    "crop":          row.get("Crop", "").strip(),
                    "area_ha":       area,
                    "production_t":  prod,
                })
            except (ValueError, KeyError):
                continue

    sql = """
        INSERT INTO pipeline_india_crop_production
            (state_name, district_name, crop_year, season, crop, area_ha, production_t)
        VALUES
            (:state_name, :district_name, :crop_year, :season, :crop, :area_ha, :production_t)
    """
    n = bulk_insert(db, sql, rows, batch=1000)
    log.info(f"  ✓ {table}: inserted {n:,} / {len(rows):,} rows")
    return n


# ══════════════════════════════════════════════════════════════════════════════
# 5. Daily Delhi Climate (sumanthvrao/daily-climate-time-series-data)
# ══════════════════════════════════════════════════════════════════════════════

def load_delhi_climate(db: Session, force: bool = False) -> int:
    """
    Loads DailyDelhiClimateTrain.csv + DailyDelhiClimateTest.csv.
    Columns: date, meantemp, humidity, wind_speed, meanpressure
    """
    table = "pipeline_delhi_climate"
    existing = table_count(db, table)
    if existing > 0 and not force:
        log.info(f"  ↳ {table}: {existing:,} rows already present, skipping")
        return 0

    base = (
        KAGGLE_CACHE
        / "sumanthvrao"
        / "daily-climate-time-series-data"
        / "versions"
        / "3"
    )
    files = [base / "DailyDelhiClimateTrain.csv", base / "DailyDelhiClimateTest.csv"]

    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.execute(text(f"""
        CREATE TABLE {table} (
            id           SERIAL PRIMARY KEY,
            obs_date     DATE,
            mean_temp_c  FLOAT,
            humidity     FLOAT,
            wind_speed   FLOAT,
            mean_pressure FLOAT,
            split        VARCHAR(10),
            source       VARCHAR(50) DEFAULT 'kaggle_sumanthvrao',
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (obs_date, split)
        )
    """))
    db.execute(text(f"CREATE INDEX ON {table} (obs_date)"))
    db.commit()

    total_rows, total_inserted = 0, 0
    for csv_path in files:
        if not csv_path.exists():
            log.warning(f"  ✗ File not found: {csv_path}")
            continue
        split = "train" if "Train" in csv_path.name else "test"
        rows = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    rows.append({
                        "obs_date":      row["date"].strip(),
                        "mean_temp_c":   float(row["meantemp"]) if row.get("meantemp") else None,
                        "humidity":      float(row["humidity"]) if row.get("humidity") else None,
                        "wind_speed":    float(row["wind_speed"]) if row.get("wind_speed") else None,
                        "mean_pressure": float(row["meanpressure"]) if row.get("meanpressure") else None,
                        "split":         split,
                    })
                except (ValueError, KeyError):
                    continue
        total_rows += len(rows)
        sql = """
            INSERT INTO pipeline_delhi_climate
                (obs_date, mean_temp_c, humidity, wind_speed, mean_pressure, split)
            VALUES
                (:obs_date, :mean_temp_c, :humidity, :wind_speed, :mean_pressure, :split)
            ON CONFLICT (obs_date, split) DO NOTHING
        """
        total_inserted += bulk_insert(db, sql, rows)

    log.info(f"  ✓ {table}: inserted {total_inserted:,} / {total_rows:,} rows")
    return total_inserted


# ══════════════════════════════════════════════════════════════════════════════
# 6. NASA POWER Weather Observations
# ══════════════════════════════════════════════════════════════════════════════

# Location metadata keyed by "lat_lon" extracted from filename
LOCATION_META = {
    "30.9_75.8":    {"name": "Punjab, India",          "country": "India",     "region": "Punjab"},
    "42.0_-93.5":   {"name": "Iowa, USA",               "country": "USA",       "region": "Iowa"},
    "28.6_77.2":    {"name": "Delhi, India",             "country": "India",     "region": "Delhi"},
    "31.5_74.3":    {"name": "Punjab, Pakistan",         "country": "Pakistan",  "region": "Punjab"},
    "34.8_113.6":   {"name": "Henan, China",             "country": "China",     "region": "Henan"},
    "-23.5_-46.6":  {"name": "São Paulo, Brazil",        "country": "Brazil",    "region": "São Paulo"},
    "-27.5_153.0":  {"name": "Queensland, Australia",    "country": "Australia", "region": "Queensland"},
    "-1.3_36.8":    {"name": "Nairobi, Kenya",           "country": "Kenya",     "region": "Nairobi"},
    "-34.6_-58.4":  {"name": "Buenos Aires, Argentina",  "country": "Argentina", "region": "Buenos Aires"},
    "13.7_100.5":   {"name": "Bangkok, Thailand",        "country": "Thailand",  "region": "Bangkok"},
    "51.5_-0.1":    {"name": "London, UK",               "country": "UK",        "region": "London"},
    "48.9_2.3":     {"name": "Paris, France",            "country": "France",    "region": "Paris"},
    "37.6_-122.4":  {"name": "California, USA",          "country": "USA",       "region": "California"},
}


def _location_from_filename(stem: str) -> tuple[float, float, dict]:
    """Extract lat, lon and metadata from filename like point_30.9_75.8_20200101_..."""
    parts = stem.split("_")
    # parts[0]="point", parts[1]=lat, parts[2]=lon, rest=dates
    lat = float(parts[1])
    lon = float(parts[2])
    key = f"{lat}_{lon}"
    meta = LOCATION_META.get(key, {
        "name": f"Location ({lat}, {lon})",
        "country": "Unknown",
        "region": "Unknown",
    })
    return lat, lon, meta


def load_nasa_power(db: Session, force: bool = False) -> int:
    """
    Loads all NASA POWER JSON files from /Volumes/S1/dataset/nasa-power/.
    Parameters: T2M (temp), PRECTOTCORR (precip), RH2M (humidity), WS2M (wind)
    """
    table = "pipeline_weather_observations"
    existing = table_count(db, table)
    if existing > 0 and not force:
        log.info(f"  ↳ {table}: {existing:,} rows already present, skipping")
        return 0

    json_files = sorted(NASA_POWER_DIR.glob("*.json"))
    if not json_files:
        log.warning(f"  ✗ No JSON files found in {NASA_POWER_DIR}")
        return 0

    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
    db.execute(text(f"""
        CREATE TABLE {table} (
            id              SERIAL PRIMARY KEY,
            location_name   VARCHAR(100),
            country         VARCHAR(100),
            region          VARCHAR(100),
            latitude        FLOAT NOT NULL,
            longitude       FLOAT NOT NULL,
            obs_date        DATE  NOT NULL,
            temperature_c   FLOAT,
            precipitation_mm FLOAT,
            humidity_pct    FLOAT,
            wind_speed_ms   FLOAT,
            source          VARCHAR(50) DEFAULT 'nasa_power',
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (latitude, longitude, obs_date, source)
        )
    """))
    db.execute(text(f"CREATE INDEX ON {table} (obs_date)"))
    db.execute(text(f"CREATE INDEX ON {table} (country)"))
    db.execute(text(f"CREATE INDEX ON {table} (latitude, longitude)"))
    db.commit()

    total_rows, total_inserted = 0, 0

    for jf in json_files:
        try:
            lat, lon, meta = _location_from_filename(jf.stem)
        except (IndexError, ValueError):
            log.warning(f"  ✗ Cannot parse filename: {jf.name}")
            continue

        with open(jf) as f:
            data = json.load(f)

        params = data.get("properties", {}).get("parameter", {})
        dates = sorted({d for p in params.values() if isinstance(p, dict) for d in p})

        rows = []
        for date_str in dates:
            try:
                obs_date = datetime.strptime(date_str, "%Y%m%d").date()
                rows.append({
                    "location_name":    meta["name"],
                    "country":          meta["country"],
                    "region":           meta["region"],
                    "latitude":         lat,
                    "longitude":        lon,
                    "obs_date":         obs_date,
                    "temperature_c":    params.get("T2M", {}).get(date_str),
                    "precipitation_mm": params.get("PRECTOTCORR", {}).get(date_str),
                    "humidity_pct":     params.get("RH2M", {}).get(date_str),
                    "wind_speed_ms":    params.get("WS2M", {}).get(date_str),
                })
            except ValueError:
                continue

        total_rows += len(rows)
        sql = """
            INSERT INTO pipeline_weather_observations
                (location_name, country, region, latitude, longitude, obs_date,
                 temperature_c, precipitation_mm, humidity_pct, wind_speed_ms, source)
            VALUES
                (:location_name, :country, :region, :latitude, :longitude, :obs_date,
                 :temperature_c, :precipitation_mm, :humidity_pct, :wind_speed_ms, 'nasa_power')
            ON CONFLICT (latitude, longitude, obs_date, source) DO NOTHING
        """
        n = bulk_insert(db, sql, rows)
        total_inserted += n
        log.info(f"    {jf.name}: {n:,} rows")

    log.info(f"  ✓ {table}: inserted {total_inserted:,} / {total_rows:,} rows total")
    return total_inserted


# ══════════════════════════════════════════════════════════════════════════════
# Registry + CLI
# ══════════════════════════════════════════════════════════════════════════════

LOADERS = {
    "yields":       (load_crop_yields,          "Kaggle: Crop Yield Prediction (~28k rows)"),
    "recommendation": (load_crop_recommendation, "Kaggle: Crop Recommendation (~2.2k rows)"),
    "fertilizer":   (load_fertilizer_prediction, "Kaggle: Fertilizer Prediction (~99 rows)"),
    "india":        (load_india_crop_production, "Kaggle: Indian Crop Production (~246k rows)"),
    "delhi":        (load_delhi_climate,         "Kaggle: Daily Delhi Climate (~14k rows)"),
    "weather":      (load_nasa_power,            "NASA POWER: Weather Observations (~68k rows)"),
}


def main():
    parser = argparse.ArgumentParser(description="Load demo datasets into BijMantra PostgreSQL")
    parser.add_argument("--force", action="store_true", help="Drop and reload even if data exists")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help=f"Comma-separated subset to load. Options: {', '.join(LOADERS)}",
    )
    parser.add_argument("--list", action="store_true", help="List available loaders and exit")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable loaders:")
        for key, (_, desc) in LOADERS.items():
            print(f"  {key:<16} {desc}")
        return

    selected = list(LOADERS.keys())
    if args.only:
        selected = [s.strip() for s in args.only.split(",")]
        unknown = [s for s in selected if s not in LOADERS]
        if unknown:
            print(f"Unknown loaders: {unknown}. Valid: {list(LOADERS)}")
            sys.exit(1)

    log.info("=" * 60)
    log.info("BijMantra Demo Dataset Loader")
    log.info(f"Dataset root : {DATASET_ROOT}")
    log.info(f"Force reload : {args.force}")
    log.info(f"Loading      : {selected}")
    log.info("=" * 60)

    if not DATASET_ROOT.exists():
        log.error(f"Dataset root not found: {DATASET_ROOT}")
        log.error("Make sure the S1 drive is mounted.")
        sys.exit(1)

    db = get_session()
    total = 0
    try:
        for key in selected:
            fn, desc = LOADERS[key]
            log.info(f"\n[{key}] {desc}")
            n = fn(db, force=args.force)
            total += n
    except Exception as e:
        log.exception(f"Fatal error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

    log.info("\n" + "=" * 60)
    log.info(f"Done. Total rows inserted: {total:,}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
