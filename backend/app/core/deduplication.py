"""
Deduplication Engine
Advanced deduplication with exact and fuzzy matching algorithms
Implements industry-standard techniques from financial data management
"""
import uuid
from typing import List, Dict, Any, Optional, Set, Tuple
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from collections import defaultdict
import hashlib

from app.models.data_quality import DuplicateRecord


class DeduplicationEngine:
    """
    Advanced deduplication engine with multiple matching strategies
    Based on best practices from Private Banking data quality management
    """

    def __init__(self, fuzzy_threshold: int = 85):
        """
        Initialize deduplication engine

        Args:
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matches
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.duplicate_groups: List[DuplicateRecord] = []

    def find_duplicates(self, df: pd.DataFrame,
                       key_columns: Optional[List[str]] = None,
                       fuzzy_columns: Optional[List[str]] = None,
                       methods: List[str] = ['exact']) -> List[DuplicateRecord]:
        """
        Find duplicate records using specified methods

        Args:
            df: DataFrame to analyze
            key_columns: Columns to use for exact matching (None = all columns)
            fuzzy_columns: Columns to use for fuzzy matching
            methods: List of methods to use ['exact', 'fuzzy', 'phonetic']

        Returns:
            List of DuplicateRecord objects
        """
        self.duplicate_groups = []

        if 'exact' in methods:
            self._find_exact_duplicates(df, key_columns)

        if 'fuzzy' in methods and fuzzy_columns:
            self._find_fuzzy_duplicates(df, fuzzy_columns)

        if 'phonetic' in methods and fuzzy_columns:
            self._find_phonetic_duplicates(df, fuzzy_columns)

        return self.duplicate_groups

    def _find_exact_duplicates(self, df: pd.DataFrame,
                              key_columns: Optional[List[str]] = None) -> None:
        """Find exact duplicate records"""
        if key_columns is None:
            key_columns = df.columns.tolist()

        # Find duplicated rows
        duplicated_mask = df.duplicated(subset=key_columns, keep=False)
        duplicated_df = df[duplicated_mask]

        if len(duplicated_df) == 0:
            return

        # Group duplicates
        for _, group_df in duplicated_df.groupby(list(key_columns)):
            if len(group_df) > 1:
                records = group_df.to_dict('records')

                duplicate_record = DuplicateRecord(
                    group_id=str(uuid.uuid4()),
                    records=records,
                    match_score=100.0,
                    match_method='exact',
                    matching_columns=key_columns
                )

                self.duplicate_groups.append(duplicate_record)

    def _find_fuzzy_duplicates(self, df: pd.DataFrame,
                              fuzzy_columns: List[str]) -> None:
        """
        Find fuzzy duplicate records using string similarity
        Particularly useful for customer names, addresses, etc.
        """
        # Create comparison groups for efficiency
        # Only compare records that might be similar
        comparison_groups = self._create_blocking_groups(df, fuzzy_columns)

        for block_key, indices in comparison_groups.items():
            if len(indices) < 2:
                continue

            block_df = df.iloc[indices]
            self._compare_within_block(block_df, fuzzy_columns)

    def _create_blocking_groups(self, df: pd.DataFrame,
                               columns: List[str]) -> Dict[str, List[int]]:
        """
        Create blocking groups to reduce comparison complexity
        Uses first N characters and soundex-like approach
        """
        groups = defaultdict(list)

        for idx, row in df.iterrows():
            # Create blocking key from first characters of key columns
            block_parts = []
            for col in columns:
                value = str(row[col]) if pd.notna(row[col]) else ""
                if value:
                    # Use first 3 characters (lowercased) as blocking key
                    block_parts.append(value.lower()[:3])

            block_key = "_".join(block_parts)
            groups[block_key].append(idx)

        return groups

    def _compare_within_block(self, block_df: pd.DataFrame,
                             fuzzy_columns: List[str]) -> None:
        """Compare records within a blocking group"""
        indices = block_df.index.tolist()
        matched_indices = set()
        groups_found = []

        for i in range(len(indices)):
            if indices[i] in matched_indices:
                continue

            current_group = [indices[i]]
            matched_indices.add(indices[i])

            for j in range(i + 1, len(indices)):
                if indices[j] in matched_indices:
                    continue

                # Calculate similarity score
                similarity = self._calculate_similarity(
                    block_df.iloc[i],
                    block_df.iloc[j],
                    fuzzy_columns
                )

                if similarity >= self.fuzzy_threshold:
                    current_group.append(indices[j])
                    matched_indices.add(indices[j])

            if len(current_group) > 1:
                # Create duplicate record
                group_records = block_df.loc[current_group].to_dict('records')
                avg_similarity = self._calculate_group_similarity(
                    block_df.loc[current_group],
                    fuzzy_columns
                )

                duplicate_record = DuplicateRecord(
                    group_id=str(uuid.uuid4()),
                    records=group_records,
                    match_score=round(avg_similarity, 2),
                    match_method='fuzzy',
                    matching_columns=fuzzy_columns
                )

                self.duplicate_groups.append(duplicate_record)

    def _calculate_similarity(self, row1: pd.Series, row2: pd.Series,
                             columns: List[str]) -> float:
        """
        Calculate overall similarity between two records
        Uses multiple similarity metrics
        """
        similarities = []

        for col in columns:
            val1 = str(row1[col]) if pd.notna(row1[col]) else ""
            val2 = str(row2[col]) if pd.notna(row2[col]) else ""

            if not val1 and not val2:
                similarities.append(100)  # Both empty = match
            elif not val1 or not val2:
                similarities.append(0)  # One empty = no match
            else:
                # Use token sort ratio for better fuzzy matching
                # This handles word order differences
                token_sort = fuzz.token_sort_ratio(val1.lower(), val2.lower())
                # Use partial ratio to handle substring matches
                partial = fuzz.partial_ratio(val1.lower(), val2.lower())
                # Use simple ratio for exact character matching
                simple = fuzz.ratio(val1.lower(), val2.lower())

                # Take weighted average favoring token_sort
                similarity = (token_sort * 0.5 + partial * 0.3 + simple * 0.2)
                similarities.append(similarity)

        # Return average similarity across all columns
        return np.mean(similarities) if similarities else 0

    def _calculate_group_similarity(self, group_df: pd.DataFrame,
                                   columns: List[str]) -> float:
        """Calculate average similarity within a group"""
        indices = group_df.index.tolist()
        similarities = []

        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                similarity = self._calculate_similarity(
                    group_df.loc[indices[i]],
                    group_df.loc[indices[j]],
                    columns
                )
                similarities.append(similarity)

        return np.mean(similarities) if similarities else 100

    def _find_phonetic_duplicates(self, df: pd.DataFrame,
                                 phonetic_columns: List[str]) -> None:
        """
        Find phonetic duplicates (soundalike names)
        Useful for customer name matching in banking
        """
        # Simple phonetic encoding (Metaphone-like)
        phonetic_groups = defaultdict(list)

        for idx, row in df.iterrows():
            phonetic_keys = []
            for col in phonetic_columns:
                value = str(row[col]) if pd.notna(row[col]) else ""
                if value:
                    # Create simple phonetic key
                    phonetic_key = self._simple_phonetic(value)
                    phonetic_keys.append(phonetic_key)

            if phonetic_keys:
                combined_key = "_".join(phonetic_keys)
                phonetic_groups[combined_key].append(idx)

        # Create duplicate records for phonetic matches
        for phonetic_key, indices in phonetic_groups.items():
            if len(indices) > 1:
                group_df = df.iloc[indices]
                records = group_df.to_dict('records')

                # Calculate actual similarity
                avg_similarity = self._calculate_group_similarity(
                    group_df,
                    phonetic_columns
                )

                duplicate_record = DuplicateRecord(
                    group_id=str(uuid.uuid4()),
                    records=records,
                    match_score=round(avg_similarity, 2),
                    match_method='phonetic',
                    matching_columns=phonetic_columns
                )

                self.duplicate_groups.append(duplicate_record)

    def _simple_phonetic(self, text: str) -> str:
        """
        Simple phonetic encoding
        Converts text to phonetic representation
        """
        text = text.upper()

        # Remove vowels except at start
        if len(text) > 1:
            text = text[0] + ''.join([c for c in text[1:] if c not in 'AEIOU'])

        # Replace similar sounding letters
        replacements = {
            'PH': 'F',
            'GH': 'F',
            'CK': 'K',
            'C': 'K',
            'Z': 'S',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove consecutive duplicates
        result = []
        prev = ''
        for char in text:
            if char != prev:
                result.append(char)
                prev = char

        return ''.join(result)[:6]  # Return first 6 characters

    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get statistics about found duplicates"""
        if not self.duplicate_groups:
            return {
                "total_groups": 0,
                "total_duplicate_records": 0,
                "by_method": {},
                "avg_group_size": 0,
                "avg_match_score": 0
            }

        total_records = sum(len(group.records) for group in self.duplicate_groups)
        method_counts = defaultdict(int)
        match_scores = []

        for group in self.duplicate_groups:
            method_counts[group.match_method] += 1
            match_scores.append(group.match_score)

        return {
            "total_groups": len(self.duplicate_groups),
            "total_duplicate_records": total_records,
            "by_method": dict(method_counts),
            "avg_group_size": round(total_records / len(self.duplicate_groups), 2),
            "avg_match_score": round(np.mean(match_scores), 2) if match_scores else 0
        }

    def merge_duplicates(self, df: pd.DataFrame,
                        strategy: str = 'first') -> pd.DataFrame:
        """
        Merge duplicate records according to specified strategy

        Args:
            df: Original DataFrame
            strategy: 'first', 'last', or 'best' (most complete record)

        Returns:
            DataFrame with duplicates merged
        """
        if not self.duplicate_groups:
            return df

        indices_to_remove = set()

        for group in self.duplicate_groups:
            group_indices = [i for i, row in enumerate(df.to_dict('records'))
                           if row in group.records]

            if len(group_indices) < 2:
                continue

            if strategy == 'first':
                # Keep first, remove rest
                indices_to_remove.update(group_indices[1:])
            elif strategy == 'last':
                # Keep last, remove rest
                indices_to_remove.update(group_indices[:-1])
            elif strategy == 'best':
                # Keep most complete record (least nulls)
                group_df = df.iloc[group_indices]
                null_counts = group_df.isnull().sum(axis=1)
                best_idx = null_counts.idxmin()

                # Remove all except best
                indices_to_remove.update([idx for idx in group_indices
                                        if idx != best_idx])

        # Return DataFrame without duplicate indices
        all_indices = set(range(len(df)))
        keep_indices = sorted(all_indices - indices_to_remove)

        return df.iloc[keep_indices].reset_index(drop=True)
