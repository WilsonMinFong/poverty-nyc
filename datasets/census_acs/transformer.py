from datasets.base import BaseDatasetTransformer
import pandas as pd
import numpy as np

class CensusACSTransformer(BaseDatasetTransformer):
    def __init__(self, config):
        super().__init__(config)
        self.census_config = config.census_config

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # Rename columns based on config mapping
        # The API returns columns like B19013_001E, B17020_001E, etc.
        # We need to map them to friendly names.
        
        # Rename columns
        df = df.rename(columns=self.census_config.variables)
        
        # Rename geography column
        if "zip code tabulation area" in df.columns:
            df = df.rename(columns={"zip code tabulation area": "zip_code"})
        
        # Convert numeric columns
        numeric_cols = ["median_household_income", "poverty_universe", "poverty_count"]
        for col in numeric_cols:
            if col in df.columns:
                # Force numeric, coercing errors to NaN (Census uses negative numbers for annotations sometimes)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Handle Census special values (e.g., -666666666) if any
                # Usually errors='coerce' handles non-numeric strings, but if they are valid numbers but sentinels:
                # We might need to filter. But let's assume standard cleaning for now.
                # Specifically for income, -666666666 means open-ended top/bottom or missing.
                df.loc[df[col] < 0, col] = np.nan

        # Calculate poverty rate
        if "poverty_count" in df.columns and "poverty_universe" in df.columns:
            df["poverty_rate"] = (df["poverty_count"] / df["poverty_universe"]) * 100
            df["poverty_rate"] = df["poverty_rate"].round(2)

        # Replace NaN with None to ensure NULL in database instead of NaN value
        cols_to_clean = ["median_household_income", "poverty_rate", "poverty_count", "poverty_universe"]
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].replace({np.nan: None})
        
        # Add year
        df["year"] = self.census_config.year
        
        # Standardize and add metadata
        df = self.add_metadata(df)
        
        return df

    def get_schema(self) -> dict:
        return self.config.data_schema.model_dump()
