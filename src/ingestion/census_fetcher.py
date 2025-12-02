"""Data fetcher for US Census API."""

import os
from typing import Dict, Any, Optional, List
import requests
import pandas as pd

from src.config.models import DatasetConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CensusFetcher:
    """Fetches data from US Census API."""

    def __init__(self, dataset_config: DatasetConfig):
        """
        Initialize the Census fetcher.

        Args:
            dataset_config: Dataset configuration
        """
        self.dataset_config = dataset_config
        self.census_config = dataset_config.census_config
        if not self.census_config:
            raise ValueError("Census configuration is missing")
            
        self.api_key = os.getenv("CENSUS_API_KEY")


    def fetch_from_api(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch data from Census API.

        Args:
            filters: Optional filter parameters (overrides config filters if provided)
            limit: Optional limit (ignored for Census API)

        Returns:
            DataFrame with fetched data
        """
        year = self.census_config.year
        dataset = self.census_config.dataset
        geography = self.census_config.geography
        variables = list(self.census_config.variables.keys())
        
        # Construct base URL
        base_url = f"https://api.census.gov/data/{year}/{dataset}"
        
        # Prepare parameters
        params = {
            "get": ",".join(variables),
            "for": geography + ":*", # Default to all if no filter
        }
        
        if self.api_key:
            params["key"] = self.api_key

        # Handle filtering by zip codes
        # Use config filters by default, but allow override from CLI
        config_filters = self.census_config.filters or {}
        active_filters = filters if filters else config_filters
        
        if active_filters and "zip_codes" in active_filters:
            zip_codes = active_filters["zip_codes"]
            return self._fetch_by_chunks(base_url, params, zip_codes)
        else:
            # Fetch all for the geography (might be too large for ZCTA nationwide, but for state it's fine)
            # For ZCTA, we usually need to filter by state or list. 
            # If no filter provided, this might fail or timeout for nationwide ZCTA.
            # But we assume we are filtering for NYC.
            logger.warning("No zip code filter provided. Attempting to fetch all ZCTAs (this may fail).")
            return self._make_request(base_url, params)

    def _fetch_by_chunks(self, base_url: str, base_params: Dict[str, str], zip_codes: List[str]) -> pd.DataFrame:
        """
        Fetch data in chunks of zip codes.
        
        Args:
            base_url: API endpoint
            base_params: Base query parameters
            zip_codes: List of zip codes to fetch
            
        Returns:
            Combined DataFrame
        """
        chunk_size = 50 # Census API URL length limit safety
        all_data = []
        
        for i in range(0, len(zip_codes), chunk_size):
            chunk = zip_codes[i:i + chunk_size]
            logger.info(f"Fetching chunk {i//chunk_size + 1} ({len(chunk)} zip codes)")
            
            # Census API for ZCTA list: &for=zip code tabulation area:10001,10002,...
            # Note: The geography param in 'for' needs to be specific.
            # For ZCTA, it is 'zip code tabulation area'.
            
            params = base_params.copy()
            params["for"] = f"zip code tabulation area:{','.join(chunk)}"
            
            try:
                df_chunk = self._make_request(base_url, params)
                all_data.append(df_chunk)
            except Exception as e:
                logger.error(f"Failed to fetch chunk: {e}")
                raise

        if not all_data:
            return pd.DataFrame()
            
        return pd.concat(all_data, ignore_index=True)

    def _make_request(self, url: str, params: Dict[str, str]) -> pd.DataFrame:
        """
        Make request to Census API and parse response.
        
        Args:
            url: API URL
            params: Query parameters
            
        Returns:
            DataFrame
        """
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or len(data) < 2:
            return pd.DataFrame()
            
        # First row is headers
        headers = data[0]
        rows = data[1:]
        
        return pd.DataFrame(rows, columns=headers)
