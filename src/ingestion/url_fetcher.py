import requests
import pandas as pd
from src.config.models import DatasetConfig
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

class UrlFetcher:
    """Fetches data from a direct URL download."""

    def __init__(self, dataset_config: DatasetConfig):
        self.dataset_config = dataset_config
        self.url_config = dataset_config.url_config
        
        if not self.url_config:
            raise ValueError("URL configuration is missing")

    def fetch_data(self, force: bool = False) -> pd.DataFrame:
        """
        Download file from URL and load into DataFrame.

        Args:
            force: If True, force re-download even if file exists

        Returns:
            DataFrame containing the data
        """
        url = self.url_config.url
        target_filename = self.url_config.filename or url.split('/')[-1]
        
        # Create raw directory for download
        raw_dir = settings.get_data_path('raw') / self.dataset_config.dataset.id
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = raw_dir / target_filename
        
        # Check if we need to download
        if not file_path.exists() or force:
            try:
                logger.info(f"Downloading file from {url}...")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"File downloaded to {file_path}")
                    
            except Exception as e:
                # Cleanup partial download if failed
                if file_path.exists():
                    file_path.unlink()
                raise e
        else:
            logger.info(f"File found at {file_path}, skipping download.")
            
        # Load data based on extension
        logger.info(f"Loading data from {file_path}")
        if str(file_path).endswith('.csv'):
            return pd.read_csv(file_path)
        elif str(file_path).endswith('.json'):
            return pd.read_json(file_path)
        else:
            try:
                return pd.read_csv(file_path)
            except:
                raise ValueError(f"Unsupported file format for {file_path}")
