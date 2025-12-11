#!/usr/bin/env python3
"""Export static GeoJSON data files for frontend consumption."""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.ingestion.storage import DataStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Output directory for static files
OUTPUT_DIR = Path(__file__).parent.parent / "viz" / "public" / "data"


def export_food_gaps(storage: DataStorage) -> dict:
    """Export food supply gaps as GeoJSON."""
    query = text("""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(
                json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(n.geom)::json,
                    'properties', json_build_object(
                        'nta_code', n.nta2020,
                        'nta_name', n.nta_name,
                        'boro_name', n.boro_name,
                        'year', f.year,
                        'supply_gap_lbs', f.supply_gap_lbs,
                        'food_insecure_pct', f.food_insecure_pct,
                        'vulnerable_pop_score', f.vulnerable_pop_score,
                        'unemployment_rate', f.unemployment_rate
                    )
                )
            )
        ) as geojson
        FROM ntas_2020 n
        LEFT JOIN food_supply_gaps f ON n.nta2020 = f.nta_code
        WHERE f.year = (SELECT MAX(year) FROM food_supply_gaps)
    """)
    
    engine = storage.get_engine()
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
    return result


def export_poverty_by_zip(storage: DataStorage) -> dict:
    """Export poverty rates as GeoJSON."""
    query = text("""
        SELECT 
            json_build_object(
                'type', 'FeatureCollection',
                'features', json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(z.geometry)::json,
                        'properties', json_build_object(
                            'zip_code', z.zip_code,
                            'year', c.year,
                            'poverty_rate', c.poverty_rate,
                            'median_household_income', c.median_household_income,
                            'poverty_count', c.poverty_count,
                            'poverty_universe', c.poverty_universe
                        )
                    )
                )
            ) as geojson
        FROM census_zctas_2020 z
        JOIN census_acs_income_poverty c ON z.zip_code = c.zip_code
        WHERE c.year = (SELECT MAX(year) FROM census_acs_income_poverty)
          AND c.poverty_rate IS NOT NULL
          AND c.median_household_income IS NOT NULL;
    """)
    
    engine = storage.get_engine()
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
    return result or {"type": "FeatureCollection", "features": []}


def export_rent_by_zip(storage: DataStorage) -> dict:
    """Export rent index as GeoJSON."""
    query = text("""
        SELECT 
            json_build_object(
                'type', 'FeatureCollection',
                'features', json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(z.geometry)::json,
                        'properties', json_build_object(
                            'zip_code', z.zip_code,
                            'rent_index', r.rent_index,
                            'date', r.date,
                            'year', EXTRACT(YEAR FROM r.date)
                        )
                    )
                )
            ) as geojson
        FROM census_zctas_2020 z
        JOIN zillow_zori r ON z.zip_code = r.zip_code
        WHERE r.rent_index IS NOT NULL;
    """)
    
    engine = storage.get_engine()
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
    return result


def main():
    """Export all static data files."""
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    storage = DataStorage()
    
    try:
        exports = [
            ("food-gaps.json", export_food_gaps),
            ("poverty-by-zip.json", export_poverty_by_zip),
            ("rent-by-zip.json", export_rent_by_zip),
        ]
        
        for filename, export_func in exports:
            logger.info(f"Exporting {filename}...")
            data = export_func(storage)
            
            output_path = OUTPUT_DIR / filename
            with open(output_path, "w") as f:
                json.dump(data, f)
            
            # Get file size
            size_kb = output_path.stat().st_size / 1024
            logger.info(f"  → {output_path} ({size_kb:.1f} KB)")
        
        logger.info("Export complete!")
        
    finally:
        storage.close()


if __name__ == "__main__":
    main()
