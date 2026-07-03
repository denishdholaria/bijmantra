"""
Weather data seeder for NASA POWER climate data.

This seeder loads NASA POWER agroclimatology data into PostgreSQL
for weather-yield correlation analysis and climate-based recommendations.

Data source: /Volumes/hfs/bijmantra-datasets/nasa-power/
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

from app.integrations.download_config import get_data_dir

logger = logging.getLogger(__name__)


# Location metadata for NASA POWER files
LOCATIONS = {
    "point_30.9_75.8": {"name": "Punjab, India", "country": "India", "region": "Punjab"},
    "point_42.0_-93.5": {"name": "Iowa, USA", "country": "USA", "region": "Iowa"},
    "point_28.6_77.2": {"name": "Delhi, India", "country": "India", "region": "Delhi"},
    "point_31.5_74.3": {"name": "Punjab, Pakistan", "country": "Pakistan", "region": "Punjab"},
    "point_34.8_113.6": {"name": "Henan, China", "country": "China", "region": "Henan"},
    "point_-23.5_-46.6": {"name": "São Paulo, Brazil", "country": "Brazil", "region": "São Paulo"},
    "point_-27.5_153.0": {"name": "Queensland, Australia", "country": "Australia", "region": "Queensland"},
    "point_-1.3_36.8": {"name": "Nairobi, Kenya", "country": "Kenya", "region": "Nairobi"},
    "point_-34.6_-58.4": {"name": "Buenos Aires, Argentina", "country": "Argentina", "region": "Buenos Aires"},
    "point_13.7_100.5": {"name": "Bangkok, Thailand", "country": "Thailand", "region": "Bangkok"},
    "point_51.5_-0.1": {"name": "London, UK", "country": "UK", "region": "London"},
    "point_48.9_2.3": {"name": "Paris, France", "country": "France", "region": "Paris"},
    "point_37.6_-122.4": {"name": "California, USA", "country": "USA", "region": "California"},
}


def create_weather_table(db: Session):
    """Create weather_observations table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS weather_observations (
        id SERIAL PRIMARY KEY,
        location_name VARCHAR(100) NOT NULL,
        country VARCHAR(100),
        region VARCHAR(100),
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL,
        observation_date DATE NOT NULL,
        temperature_c FLOAT,
        precipitation_mm FLOAT,
        humidity_percent FLOAT,
        wind_speed_ms FLOAT,
        solar_radiation_mj FLOAT,
        source VARCHAR(50) DEFAULT 'NASA_POWER',
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(latitude, longitude, observation_date, source)
    );
    
    CREATE INDEX IF NOT EXISTS idx_weather_location_date 
        ON weather_observations(latitude, longitude, observation_date);
    CREATE INDEX IF NOT EXISTS idx_weather_date 
        ON weather_observations(observation_date);
    CREATE INDEX IF NOT EXISTS idx_weather_country 
        ON weather_observations(country);
    """
    
    db.execute(text(create_table_sql))
    db.commit()
    logger.info("✓ Weather observations table created/verified")


def parse_nasa_power_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a NASA POWER JSON file and extract weather observations.
    
    Args:
        file_path: Path to NASA POWER JSON file
        
    Returns:
        List of weather observation dictionaries
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract metadata
    geometry = data.get('geometry', {})
    coordinates = geometry.get('coordinates', [])
    if len(coordinates) >= 2:
        longitude, latitude = coordinates[0], coordinates[1]
    else:
        # Try to extract from filename
        filename = file_path.stem
        parts = filename.split('_')
        if len(parts) >= 3:
            latitude = float(parts[1])
            longitude = float(parts[2])
        else:
            logger.warning(f"Could not extract coordinates from {file_path}")
            return []
    
    # Get location metadata
    location_key = f"point_{latitude}_{longitude}"
    location_info = LOCATIONS.get(location_key, {
        "name": f"Location ({latitude}, {longitude})",
        "country": "Unknown",
        "region": "Unknown"
    })
    
    # Extract parameters
    parameters = data.get('properties', {}).get('parameter', {})
    
    # Get all dates (keys are YYYYMMDD format)
    dates = set()
    for param_data in parameters.values():
        if isinstance(param_data, dict):
            dates.update(param_data.keys())
    
    dates = sorted(dates)
    
    # Build observations
    observations = []
    for date_str in dates:
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y%m%d').date()
            
            # Extract parameters for this date
            obs = {
                'location_name': location_info['name'],
                'country': location_info['country'],
                'region': location_info['region'],
                'latitude': latitude,
                'longitude': longitude,
                'observation_date': date_obj,
                'temperature_c': parameters.get('T2M', {}).get(date_str),
                'precipitation_mm': parameters.get('PRECTOTCORR', {}).get(date_str),
                'humidity_percent': parameters.get('RH2M', {}).get(date_str),
                'wind_speed_ms': parameters.get('WS2M', {}).get(date_str),
                'solar_radiation_mj': parameters.get('ALLSKY_SFC_SW_DWN', {}).get(date_str),
                'source': 'NASA_POWER'
            }
            
            observations.append(obs)
            
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
            continue
    
    return observations


def seed_weather_data(db: Session, force: bool = False):
    """
    Seed weather observations from NASA POWER data.
    
    Args:
        db: Database session
        force: If True, delete existing data before seeding
    """
    logger.info("Starting weather data seeding from NASA POWER...")
    
    # Create table
    create_weather_table(db)
    
    # Clear existing data if force=True
    if force:
        logger.info("Clearing existing weather data...")
        db.execute(text("DELETE FROM weather_observations WHERE source = 'NASA_POWER'"))
        db.commit()
    
    # Get NASA POWER data directory
    nasa_power_dir = get_data_dir("nasa_power")
    
    if not nasa_power_dir.exists():
        logger.error(f"NASA POWER data directory not found: {nasa_power_dir}")
        return
    
    # Find all JSON files
    json_files = list(nasa_power_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {nasa_power_dir}")
        return
    
    logger.info(f"Found {len(json_files)} NASA POWER data files")
    
    # Process each file
    total_observations = 0
    total_inserted = 0
    
    for json_file in json_files:
        logger.info(f"Processing {json_file.name}...")
        
        try:
            observations = parse_nasa_power_file(json_file)
            total_observations += len(observations)
            
            # Insert observations (skip duplicates)
            inserted = 0
            for obs in observations:
                try:
                    insert_sql = """
                    INSERT INTO weather_observations 
                        (location_name, country, region, latitude, longitude, 
                         observation_date, temperature_c, precipitation_mm, 
                         humidity_percent, wind_speed_ms, solar_radiation_mj, source)
                    VALUES 
                        (:location_name, :country, :region, :latitude, :longitude,
                         :observation_date, :temperature_c, :precipitation_mm,
                         :humidity_percent, :wind_speed_ms, :solar_radiation_mj, :source)
                    ON CONFLICT (latitude, longitude, observation_date, source) DO NOTHING
                    """
                    
                    result = db.execute(text(insert_sql), obs)
                    if result.rowcount > 0:
                        inserted += 1
                    
                except Exception as e:
                    logger.warning(f"Error inserting observation: {e}")
                    continue
            
            db.commit()
            total_inserted += inserted
            logger.info(f"  ✓ Inserted {inserted}/{len(observations)} observations")
            
        except Exception as e:
            logger.error(f"Error processing {json_file.name}: {e}")
            db.rollback()
            continue
    
    logger.info(f"✓ Weather seeding complete!")
    logger.info(f"  Total observations processed: {total_observations}")
    logger.info(f"  Total observations inserted: {total_inserted}")
    
    # Show summary
    summary_sql = """
    SELECT 
        country,
        COUNT(*) as observation_count,
        MIN(observation_date) as earliest_date,
        MAX(observation_date) as latest_date
    FROM weather_observations
    WHERE source = 'NASA_POWER'
    GROUP BY country
    ORDER BY observation_count DESC
    """
    
    result = db.execute(text(summary_sql))
    rows = result.fetchall()
    
    logger.info("\nWeather Data Summary by Country:")
    for row in rows:
        logger.info(f"  {row[0]:20} {row[1]:8,} observations ({row[2]} to {row[3]})")


def main():
    """Main entry point for weather seeding."""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    force = '--force' in sys.argv
    
    # Create database session
    from app.core.config import settings
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        seed_weather_data(db, force=force)
    finally:
        db.close()


if __name__ == "__main__":
    main()
