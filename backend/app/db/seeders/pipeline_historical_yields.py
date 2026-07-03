"""
Historical yields seeder for Our World in Data crop yield data.

This seeder loads clean, analysis-ready historical crop yield data
for trend analysis, visualization, and benchmarking.

Data source: /Volumes/hfs/bijmantra-datasets/ourworldindata/
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

from app.integrations.download_config import BIJMANTRA_DATASETS_DIR

logger = logging.getLogger(__name__)


def create_historical_yields_table(db: Session):
    """Create historical_yields table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS historical_yields (
        id SERIAL PRIMARY KEY,
        country VARCHAR(100) NOT NULL,
        crop VARCHAR(100) NOT NULL,
        year INTEGER NOT NULL,
        yield_tonnes_per_ha FLOAT NOT NULL,
        source VARCHAR(50) DEFAULT 'OurWorldInData',
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(country, crop, year, source)
    );
    
    CREATE INDEX IF NOT EXISTS idx_historical_yields_country 
        ON historical_yields(country);
    CREATE INDEX IF NOT EXISTS idx_historical_yields_crop 
        ON historical_yields(crop);
    CREATE INDEX IF NOT EXISTS idx_historical_yields_year 
        ON historical_yields(year);
    CREATE INDEX IF NOT EXISTS idx_historical_yields_country_crop 
        ON historical_yields(country, crop);
    """
    
    db.execute(text(create_table_sql))
    db.commit()
    logger.info("✓ Historical yields table created/verified")


def parse_ourworldindata_csv(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse Our World in Data crop yields CSV file.
    
    Expected columns: Entity, Year, Crop, Yield (tonnes per hectare)
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of yield record dictionaries
    """
    records = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Extract fields (column names may vary)
                country = row.get('Entity') or row.get('Country') or row.get('country')
                year = row.get('Year') or row.get('year')
                crop = row.get('Crop') or row.get('crop')
                
                # Yield column might have different names
                yield_value = (
                    row.get('Yield (tonnes per hectare)') or
                    row.get('Yield') or
                    row.get('yield') or
                    row.get('yield_tonnes_per_ha')
                )
                
                if not all([country, year, crop, yield_value]):
                    logger.warning(f"Skipping incomplete row: {row}")
                    continue
                
                record = {
                    'country': country.strip(),
                    'crop': crop.strip(),
                    'year': int(year),
                    'yield_tonnes_per_ha': float(yield_value),
                    'source': 'OurWorldInData'
                }
                
                records.append(record)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing row {row}: {e}")
                continue
    
    return records


def seed_historical_yields(db: Session, force: bool = False):
    """
    Seed historical yield data from Our World in Data.
    
    Args:
        db: Database session
        force: If True, delete existing data before seeding
    """
    logger.info("Starting historical yields seeding from Our World in Data...")
    
    # Create table
    create_historical_yields_table(db)
    
    # Clear existing data if force=True
    if force:
        logger.info("Clearing existing historical yields data...")
        db.execute(text("DELETE FROM historical_yields WHERE source = 'OurWorldInData'"))
        db.commit()
    
    # Get Our World in Data directory
    owid_dir = BIJMANTRA_DATASETS_DIR / "ourworldindata"
    
    if not owid_dir.exists():
        logger.error(f"Our World in Data directory not found: {owid_dir}")
        return
    
    # Find CSV files
    csv_files = list(owid_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {owid_dir}")
        return
    
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # Process each file
    total_records = 0
    total_inserted = 0
    
    for csv_file in csv_files:
        logger.info(f"Processing {csv_file.name}...")
        
        try:
            records = parse_ourworldindata_csv(csv_file)
            total_records += len(records)
            
            # Insert records (skip duplicates)
            inserted = 0
            for record in records:
                try:
                    insert_sql = """
                    INSERT INTO historical_yields 
                        (country, crop, year, yield_tonnes_per_ha, source)
                    VALUES 
                        (:country, :crop, :year, :yield_tonnes_per_ha, :source)
                    ON CONFLICT (country, crop, year, source) DO NOTHING
                    """
                    
                    result = db.execute(text(insert_sql), record)
                    if result.rowcount > 0:
                        inserted += 1
                    
                except Exception as e:
                    logger.warning(f"Error inserting record: {e}")
                    continue
            
            db.commit()
            total_inserted += inserted
            logger.info(f"  ✓ Inserted {inserted}/{len(records)} records")
            
        except Exception as e:
            logger.error(f"Error processing {csv_file.name}: {e}")
            db.rollback()
            continue
    
    logger.info(f"✓ Historical yields seeding complete!")
    logger.info(f"  Total records processed: {total_records}")
    logger.info(f"  Total records inserted: {total_inserted}")
    
    # Show summary
    summary_sql = """
    SELECT 
        crop,
        COUNT(DISTINCT country) as country_count,
        COUNT(*) as record_count,
        MIN(year) as earliest_year,
        MAX(year) as latest_year,
        ROUND(AVG(yield_tonnes_per_ha)::numeric, 2) as avg_yield
    FROM historical_yields
    WHERE source = 'OurWorldInData'
    GROUP BY crop
    ORDER BY record_count DESC
    LIMIT 20
    """
    
    result = db.execute(text(summary_sql))
    rows = result.fetchall()
    
    logger.info("\nHistorical Yields Summary by Crop (Top 20):")
    logger.info(f"{'Crop':<30} {'Countries':>10} {'Records':>10} {'Years':>15} {'Avg Yield':>12}")
    logger.info("-" * 80)
    for row in rows:
        year_range = f"{row[3]}-{row[4]}"
        logger.info(f"{row[0]:<30} {row[1]:>10} {row[2]:>10,} {year_range:>15} {row[5]:>12}")


def main():
    """Main entry point for historical yields seeding."""
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
        seed_historical_yields(db, force=force)
    finally:
        db.close()


if __name__ == "__main__":
    main()
