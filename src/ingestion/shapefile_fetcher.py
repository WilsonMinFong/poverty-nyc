"""Generic fetcher for downloading and extracting shapefiles."""

import os
import zipfile
import requests
import geopandas as gpd

from src.config.models import DatasetConfig
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ShapefileFetcher:
    """Fetches and extracts shapefiles from a URL."""

    def __init__(self, dataset_config: DatasetConfig):
        """
        Initialize the fetcher.

        Args:
            dataset_config: Dataset configuration
        """
        self.dataset_config = dataset_config
        self.shapefile_config = dataset_config.shapefile_config
        
        if not self.shapefile_config:
            raise ValueError("Shapefile configuration is missing")

    def fetch_data(self, force: bool = False) -> gpd.GeoDataFrame:
        """
        Download zip, extract, and load shapefile into GeoDataFrame.

        Args:
            force: If True, force re-download even if file exists

        Returns:
            GeoDataFrame
        """
        url = self.shapefile_config.url
        target_filename = self.shapefile_config.filename
        
        # Create temporary directory for download
        temp_dir = settings.get_data_path('raw') / 'temp_shapefiles' / self.dataset_config.dataset.id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        shp_path = temp_dir / target_filename
        
        # Check if we need to download
        if not shp_path.exists() or force:
            zip_path = temp_dir / "download.zip"
            
            try:
                # Download file
                logger.info(f"Downloading shapefile from {url}...")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract zip
                logger.info("Extracting zip file...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    
            finally:
                # Cleanup zip file
                if zip_path.exists():
                    zip_path.unlink()
        else:
            logger.info(f"Shapefile found at {shp_path}, skipping download.")
            
        # Find the .shp file if target not found (e.g. if filename config was wrong but we just extracted)
        if not shp_path.exists():
            # Try to find any .shp file if specific one not found
            shp_files = list(temp_dir.glob("*.shp"))
            if shp_files:
                shp_path = shp_files[0]
                logger.warning(f"Specified filename {target_filename} not found, using {shp_path.name}")
            else:
                raise FileNotFoundError(f"No .shp file found in {temp_dir}")
        
        # Load into GeoDataFrame
        logger.info(f"Loading shapefile: {shp_path}")
        gdf = gpd.read_file(shp_path)
        
        return gdf
