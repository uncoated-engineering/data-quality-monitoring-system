"""
Data Quality Engine
Core engine for performing data quality checks across all dimensions
"""
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from collections import defaultdict

from app.models.data_quality import (
    QualityDimension, QualityMetric, QualityScore, ValidationResult,
    DatasetProfile, DuplicateRecord, Alert, AlertSeverity, QualityRule
)


class DataQualityEngine:
    """
    Main engine for data quality assessment
    Implements industry-standard quality dimensions
    """

    def __init__(self):
        self.rules: List[QualityRule] = []
        self.alerts: List[Alert] = []

    def assess_quality(self, df: pd.DataFrame, dataset_id: str, dataset_name: str,
                      rules: Optional[List[QualityRule]] = None) -> QualityScore:
        """
        Perform comprehensive quality assessment

        Args:
            df: DataFrame to assess
            dataset_id: Unique identifier for the dataset
            dataset_name: Human-readable dataset name
            rules: Optional list of quality rules to apply

        Returns:
            QualityScore with complete assessment results
        """
        self.rules = rules or []
        self.alerts = []
        timestamp = datetime.now()

        # Perform all quality checks
        completeness_metrics = self._check_completeness(df)
        accuracy_metrics = self._check_accuracy(df)
        consistency_metrics = self._check_consistency(df)
        uniqueness_metrics = self._check_uniqueness(df)
        validity_metrics = self._check_validity(df)

        # Combine all metrics
        all_metrics = (
            completeness_metrics +
            accuracy_metrics +
            consistency_metrics +
            uniqueness_metrics +
            validity_metrics
        )

        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(all_metrics)

        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(dimension_scores)

        # Apply rules and generate alerts
        passed_rules, failed_rules, warnings = self._apply_rules(
            all_metrics, dimension_scores
        )

        return QualityScore(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            timestamp=timestamp,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            total_records=len(df),
            metrics=all_metrics,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings
        )

    def _check_completeness(self, df: pd.DataFrame) -> List[QualityMetric]:
        """Check data completeness (missing values, null rates)"""
        metrics = []
        timestamp = datetime.now()

        # Overall completeness
        total_cells = df.size
        non_null_cells = df.count().sum()
        completeness_rate = (non_null_cells / total_cells * 100) if total_cells > 0 else 0

        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.COMPLETENESS,
            name="Overall Completeness",
            value=round(completeness_rate, 2),
            timestamp=timestamp,
            details={
                "total_cells": total_cells,
                "non_null_cells": int(non_null_cells),
                "null_cells": total_cells - int(non_null_cells)
            }
        ))

        # Per-column completeness
        column_completeness = {}
        for column in df.columns:
            non_null_count = df[column].count()
            total_count = len(df)
            completeness = (non_null_count / total_count * 100) if total_count > 0 else 0
            column_completeness[column] = round(completeness, 2)

        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.COMPLETENESS,
            name="Column Completeness",
            value=round(np.mean(list(column_completeness.values())), 2),
            timestamp=timestamp,
            details={"by_column": column_completeness}
        ))

        # Empty string check (for string columns)
        empty_string_counts = {}
        for column in df.select_dtypes(include=['object']).columns:
            empty_count = df[column].astype(str).str.strip().eq('').sum()
            if empty_count > 0:
                empty_string_counts[column] = int(empty_count)

        if empty_string_counts:
            total_empty = sum(empty_string_counts.values())
            empty_rate = (total_empty / total_cells) * 100
            metrics.append(QualityMetric(
                metric_id=str(uuid.uuid4()),
                dimension=QualityDimension.COMPLETENESS,
                name="Empty String Rate",
                value=round(100 - empty_rate, 2),
                timestamp=timestamp,
                details={"empty_strings": empty_string_counts}
            ))

        return metrics

    def _check_accuracy(self, df: pd.DataFrame) -> List[QualityMetric]:
        """Check data accuracy (data types, ranges, formats)"""
        metrics = []
        timestamp = datetime.now()

        # Data type consistency
        type_consistency = {}
        for column in df.columns:
            # Check if column has mixed types
            col_types = df[column].dropna().apply(type).value_counts()
            if len(col_types) > 1:
                type_consistency[column] = {
                    "expected": str(col_types.index[0]),
                    "violations": int(col_types.sum() - col_types.iloc[0])
                }

        type_score = 100 - (len(type_consistency) / len(df.columns) * 100) if len(df.columns) > 0 else 100
        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.ACCURACY,
            name="Data Type Consistency",
            value=round(type_score, 2),
            timestamp=timestamp,
            details={"inconsistencies": type_consistency}
        ))

        # Numeric range validation
        numeric_outliers = {}
        for column in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = df[
                (df[column] < (Q1 - 1.5 * IQR)) |
                (df[column] > (Q3 + 1.5 * IQR))
            ][column].count()

            if outlier_count > 0:
                numeric_outliers[column] = {
                    "count": int(outlier_count),
                    "percentage": round(outlier_count / len(df) * 100, 2)
                }

        outlier_rate = sum(v["count"] for v in numeric_outliers.values()) / len(df) if len(df) > 0 else 0
        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.ACCURACY,
            name="Numeric Range Accuracy",
            value=round(100 - (outlier_rate * 100), 2),
            timestamp=timestamp,
            details={"outliers": numeric_outliers}
        ))

        # Format validation for common patterns
        format_validation = self._validate_formats(df)
        if format_validation:
            metrics.append(QualityMetric(
                metric_id=str(uuid.uuid4()),
                dimension=QualityDimension.ACCURACY,
                name="Format Accuracy",
                value=round(format_validation["score"], 2),
                timestamp=timestamp,
                details=format_validation["details"]
            ))

        return metrics

    def _check_consistency(self, df: pd.DataFrame) -> List[QualityMetric]:
        """Check data consistency (cross-field validation, referential integrity)"""
        metrics = []
        timestamp = datetime.now()

        # Check for consistent capitalization in string columns
        case_consistency = {}
        for column in df.select_dtypes(include=['object']).columns:
            non_null_values = df[column].dropna()
            if len(non_null_values) > 0:
                # Check if values are consistently capitalized
                has_mixed_case = non_null_values.apply(
                    lambda x: str(x) != str(x).lower() and
                             str(x) != str(x).upper() and
                             str(x) != str(x).title()
                ).any()

                if has_mixed_case:
                    case_consistency[column] = "inconsistent"

        consistency_score = 100 - (len(case_consistency) / len(df.columns) * 100) if len(df.columns) > 0 else 100
        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.CONSISTENCY,
            name="Case Consistency",
            value=round(consistency_score, 2),
            timestamp=timestamp,
            details={"inconsistent_columns": list(case_consistency.keys())}
        ))

        # Check for consistent date formats
        date_consistency = self._check_date_consistency(df)
        if date_consistency:
            metrics.append(QualityMetric(
                metric_id=str(uuid.uuid4()),
                dimension=QualityDimension.CONSISTENCY,
                name="Date Format Consistency",
                value=round(date_consistency["score"], 2),
                timestamp=timestamp,
                details=date_consistency["details"]
            ))

        # Cross-field consistency
        cross_field_score = self._check_cross_field_consistency(df)
        if cross_field_score:
            metrics.append(QualityMetric(
                metric_id=str(uuid.uuid4()),
                dimension=QualityDimension.CONSISTENCY,
                name="Cross-Field Consistency",
                value=round(cross_field_score["score"], 2),
                timestamp=timestamp,
                details=cross_field_score["details"]
            ))

        return metrics

    def _check_uniqueness(self, df: pd.DataFrame) -> List[QualityMetric]:
        """Check data uniqueness (duplicates)"""
        metrics = []
        timestamp = datetime.now()

        # Overall duplicate check
        duplicate_rows = df.duplicated().sum()
        uniqueness_rate = (1 - duplicate_rows / len(df)) * 100 if len(df) > 0 else 100

        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.UNIQUENESS,
            name="Row Uniqueness",
            value=round(uniqueness_rate, 2),
            timestamp=timestamp,
            details={
                "duplicate_rows": int(duplicate_rows),
                "unique_rows": len(df) - int(duplicate_rows),
                "total_rows": len(df)
            }
        ))

        # Per-column uniqueness
        column_uniqueness = {}
        for column in df.columns:
            unique_count = df[column].nunique()
            total_count = df[column].count()
            uniqueness = (unique_count / total_count * 100) if total_count > 0 else 0
            column_uniqueness[column] = round(uniqueness, 2)

        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.UNIQUENESS,
            name="Column Uniqueness",
            value=round(np.mean(list(column_uniqueness.values())), 2),
            timestamp=timestamp,
            details={"by_column": column_uniqueness}
        ))

        return metrics

    def _check_validity(self, df: pd.DataFrame) -> List[QualityMetric]:
        """Check data validity (domain constraints, business rules)"""
        metrics = []
        timestamp = datetime.now()

        # Check for negative values in columns that shouldn't have them
        negative_checks = {}
        amount_columns = [col for col in df.columns if
                         any(keyword in col.lower() for keyword in
                             ['amount', 'balance', 'value', 'price', 'cost', 'revenue'])]

        for column in amount_columns:
            if df[column].dtype in [np.int64, np.float64]:
                negative_count = (df[column] < 0).sum()
                if negative_count > 0:
                    negative_checks[column] = int(negative_count)

        validity_score = 100
        if amount_columns:
            total_violations = sum(negative_checks.values())
            total_values = len(df) * len(amount_columns)
            validity_score = (1 - total_violations / total_values) * 100 if total_values > 0 else 100

        metrics.append(QualityMetric(
            metric_id=str(uuid.uuid4()),
            dimension=QualityDimension.VALIDITY,
            name="Business Rule Validity",
            value=round(validity_score, 2),
            timestamp=timestamp,
            details={"negative_amount_violations": negative_checks}
        ))

        return metrics

    def _validate_formats(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Validate common data formats (email, phone, etc.)"""
        format_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?1?\d{9,15}$',
            'zip': r'^\d{5}(-\d{4})?$'
        }

        violations = {}
        total_checks = 0
        total_violations = 0

        for column in df.select_dtypes(include=['object']).columns:
            col_lower = column.lower()

            for pattern_name, pattern in format_patterns.items():
                if pattern_name in col_lower:
                    non_null_values = df[column].dropna()
                    if len(non_null_values) > 0:
                        invalid = ~non_null_values.astype(str).str.match(pattern)
                        invalid_count = invalid.sum()

                        if invalid_count > 0:
                            violations[column] = {
                                "expected_format": pattern_name,
                                "violations": int(invalid_count),
                                "percentage": round(invalid_count / len(non_null_values) * 100, 2)
                            }

                        total_checks += len(non_null_values)
                        total_violations += invalid_count

        if total_checks > 0:
            score = (1 - total_violations / total_checks) * 100
            return {
                "score": score,
                "details": violations
            }

        return None

    def _check_date_consistency(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Check consistency of date formats"""
        date_columns = [col for col in df.columns if
                       any(keyword in col.lower() for keyword in
                           ['date', 'time', 'timestamp', 'created', 'updated'])]

        if not date_columns:
            return None

        inconsistencies = {}
        for column in date_columns:
            if df[column].dtype == 'object':
                # Check if dates can be parsed consistently
                try:
                    pd.to_datetime(df[column], errors='coerce')
                except:
                    inconsistencies[column] = "unparseable"

        score = 100 - (len(inconsistencies) / len(date_columns) * 100) if date_columns else 100
        return {
            "score": score,
            "details": {"inconsistent_columns": list(inconsistencies.keys())}
        }

    def _check_cross_field_consistency(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Check consistency across related fields"""
        violations = []

        # Example: Check if start_date < end_date
        date_pairs = [
            ('start_date', 'end_date'),
            ('created_at', 'updated_at'),
            ('open_date', 'close_date')
        ]

        for start_col, end_col in date_pairs:
            if start_col in df.columns and end_col in df.columns:
                try:
                    start_dates = pd.to_datetime(df[start_col], errors='coerce')
                    end_dates = pd.to_datetime(df[end_col], errors='coerce')

                    invalid = (start_dates > end_dates) & start_dates.notna() & end_dates.notna()
                    invalid_count = invalid.sum()

                    if invalid_count > 0:
                        violations.append({
                            "fields": f"{start_col} > {end_col}",
                            "count": int(invalid_count)
                        })
                except:
                    pass

        if violations:
            total_violations = sum(v["count"] for v in violations)
            score = (1 - total_violations / len(df)) * 100 if len(df) > 0 else 100
            return {
                "score": score,
                "details": {"violations": violations}
            }

        return {"score": 100.0, "details": {"violations": []}}

    def _calculate_dimension_scores(self, metrics: List[QualityMetric]) -> Dict[QualityDimension, float]:
        """Calculate average score per dimension"""
        dimension_scores = defaultdict(list)

        for metric in metrics:
            dimension_scores[metric.dimension].append(metric.value)

        return {
            dimension: round(np.mean(scores), 2)
            for dimension, scores in dimension_scores.items()
        }

    def _calculate_overall_score(self, dimension_scores: Dict[QualityDimension, float]) -> float:
        """Calculate weighted overall quality score"""
        # Weights based on business importance
        weights = {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.CONSISTENCY: 0.20,
            QualityDimension.UNIQUENESS: 0.15,
            QualityDimension.VALIDITY: 0.15
        }

        total_score = 0
        total_weight = 0

        for dimension, score in dimension_scores.items():
            weight = weights.get(dimension, 0.1)
            total_score += score * weight
            total_weight += weight

        return round(total_score / total_weight, 2) if total_weight > 0 else 0

    def _apply_rules(self, metrics: List[QualityMetric],
                    dimension_scores: Dict[QualityDimension, float]) -> Tuple[int, int, int]:
        """Apply quality rules and generate alerts"""
        passed = 0
        failed = 0
        warnings = 0

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Get relevant score
            if rule.column:
                # Column-specific rule
                relevant_metrics = [m for m in metrics if
                                  m.dimension == rule.dimension and
                                  rule.column in m.details.get('by_column', {})]
                if relevant_metrics:
                    score = relevant_metrics[0].details['by_column'][rule.column]
                else:
                    continue
            else:
                # Dimension-level rule
                score = dimension_scores.get(rule.dimension, 0)

            # Check threshold
            if score < rule.threshold:
                failed += 1

                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    severity=rule.severity,
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    dimension=rule.dimension,
                    message=f"{rule.name} failed: Score {score}% below threshold {rule.threshold}%",
                    dataset_id="",  # Will be set by caller
                    metric_value=score,
                    threshold=rule.threshold,
                    details=rule.parameters
                )

                self.alerts.append(alert)

                if rule.severity == AlertSeverity.WARNING:
                    warnings += 1
            else:
                passed += 1

        return passed, failed, warnings

    def get_alerts(self) -> List[Alert]:
        """Get all generated alerts"""
        return self.alerts
