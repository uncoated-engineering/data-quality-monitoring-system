"""
Data Profiler Service
Generates comprehensive statistical profiles of datasets
"""
import uuid
from datetime import datetime
from typing import Dict, Any
import pandas as pd
import numpy as np

from app.models.data_quality import DatasetProfile
from app.core.deduplication import DeduplicationEngine


class DataProfiler:
    """
    Generate statistical profiles and metadata for datasets
    """

    def __init__(self):
        self.dedup_engine = DeduplicationEngine()

    def profile_dataset(self, df: pd.DataFrame, dataset_id: str,
                       dataset_name: str) -> DatasetProfile:
        """
        Create comprehensive profile of a dataset

        Args:
            df: DataFrame to profile
            dataset_id: Unique identifier
            dataset_name: Human-readable name

        Returns:
            DatasetProfile with complete statistical information
        """
        column_profiles = {}

        for column in df.columns:
            column_profiles[column] = self._profile_column(df[column])

        # Find duplicates
        duplicates = self.dedup_engine.find_duplicates(df, methods=['exact'])
        duplicate_count = sum(len(dup.records) for dup in duplicates) - len(duplicates)
        duplicate_percentage = (duplicate_count / len(df) * 100) if len(df) > 0 else 0

        return DatasetProfile(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            total_records=len(df),
            total_columns=len(df.columns),
            timestamp=datetime.now(),
            column_profiles=column_profiles,
            duplicate_count=duplicate_count,
            duplicate_percentage=round(duplicate_percentage, 2)
        )

    def _profile_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile a single column"""
        profile = {
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percentage": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0,
            "unique_count": int(series.nunique()),
            "unique_percentage": round(series.nunique() / series.count() * 100, 2) if series.count() > 0 else 0
        }

        # Numeric statistics
        if pd.api.types.is_numeric_dtype(series):
            profile.update({
                "mean": float(series.mean()) if not series.isna().all() else None,
                "median": float(series.median()) if not series.isna().all() else None,
                "std": float(series.std()) if not series.isna().all() else None,
                "min": float(series.min()) if not series.isna().all() else None,
                "max": float(series.max()) if not series.isna().all() else None,
                "q25": float(series.quantile(0.25)) if not series.isna().all() else None,
                "q75": float(series.quantile(0.75)) if not series.isna().all() else None
            })

        # String statistics
        elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            non_null = series.dropna().astype(str)
            if len(non_null) > 0:
                profile.update({
                    "min_length": int(non_null.str.len().min()),
                    "max_length": int(non_null.str.len().max()),
                    "avg_length": round(non_null.str.len().mean(), 2),
                    "mode": str(series.mode()[0]) if len(series.mode()) > 0 else None
                })

        # Top values (for all types)
        if series.count() > 0:
            top_values = series.value_counts().head(5).to_dict()
            # Convert keys to strings for JSON serialization
            profile["top_values"] = {str(k): int(v) for k, v in top_values.items()}

        return profile
