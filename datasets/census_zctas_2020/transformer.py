from datasets.base import BaseDatasetTransformer
import pandas as pd
import geopandas as gpd
from shapely import wkt
from src.config.settings import settings

class CensusZctas2020Transformer(BaseDatasetTransformer):
    def __init__(self, config):
        super().__init__(config)
        # Load NYC zip codes from census_acs config to filter
        try:
            census_acs_config = settings.get_dataset_config('census_acs')
            self.nyc_zip_codes = census_acs_config.census_config.filters['zip_codes']
        except Exception as e:
            raise ValueError(f"Could not load NYC zip codes from census_acs config: {e}")

    def transform(self, gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        gdf_nyc = gdf[gdf['ZCTA5CE20'].isin(self.nyc_zip_codes)].copy()
        
        gdf_nyc = gdf_nyc.rename(columns={'ZCTA5CE20': 'zip_code', 'geometry': 'geometry'})
        
        # Select only required columns
        gdf_nyc = gdf_nyc[['zip_code', 'geometry']]
        
        # Ensure we are working with a DataFrame for the return type
        df = pd.DataFrame(gdf_nyc)
        
        # IMPORTANT: We must ensure the CRS is 4326 before WKT conversion
        if gdf_nyc.crs != "EPSG:4326":
            gdf_nyc = gdf_nyc.to_crs("EPSG:4326")
            
        df['geometry'] = gdf_nyc['geometry'].apply(lambda x: x.wkt)
        
        # Add metadata
        df = self.add_metadata(df)
        
        return df

    def get_schema(self) -> dict:
        return self.config.data_schema.model_dump()
