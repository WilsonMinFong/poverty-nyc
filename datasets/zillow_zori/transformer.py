from datasets.base import BaseDatasetTransformer
import pandas as pd

class ZillowZoriTransformer(BaseDatasetTransformer):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        nyc_zips = self._get_nyc_zip_codes()
        
        # Filter for NYC ZIP codes
        df['RegionName'] = df['RegionName'].astype(str)
        df = df[df['RegionName'].isin(nyc_zips)]
        
        # The CSV is wide format: RegionID, RegionName, RegionType, StateName, State, City, Metro, CountyName, [Dates...]
        metadata_cols = ['RegionID', 'RegionName', 'RegionType', 'StateName', 'State', 'City', 'Metro', 'CountyName', 'SizeRank']
        date_cols = [c for c in df.columns if c not in metadata_cols]
        
        # Melt
        df_melted = df.melt(id_vars=['RegionName'], value_vars=date_cols, var_name='date', value_name='rent_index')
        
        # Convert date to datetime
        df_melted['date'] = pd.to_datetime(df_melted['date'])
        
        # Drop rows with missing rent index
        df_melted = df_melted.dropna(subset=['rent_index'])
        
        # Sort by date descending to get latest
        df_melted = df_melted.sort_values('date', ascending=False)
        
        # Keep only the latest date for each ZIP code
        df_latest = df_melted.groupby('RegionName').first().reset_index()
        
        # Rename columns to match schema
        df_latest = df_latest.rename(columns={'RegionName': 'zip_code'})
        
        # Select final columns
        final_df = df_latest[['zip_code', 'rent_index', 'date']]
        
        # Add metadata
        final_df = self.add_metadata(final_df)
        
        return final_df

    def _get_nyc_zip_codes(self):
        """Load NYC ZIP codes from constants."""
        from src.constants import NYC_ZIP_CODES
        return NYC_ZIP_CODES

    def get_schema(self) -> dict:
        return self.config.data_schema.model_dump()
