"""
Data Quality Models
Defines data structures for quality metrics, rules, and reports
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class QualityDimension(str, Enum):
    """Data quality dimensions based on industry standards"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class DataType(str, Enum):
    """Supported data types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"


class QualityRule(BaseModel):
    """Definition of a data quality rule"""
    rule_id: str
    name: str
    dimension: QualityDimension
    description: str
    column: Optional[str] = None
    threshold: float = Field(ge=0, le=100, description="Threshold percentage")
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)


class QualityMetric(BaseModel):
    """Individual quality metric result"""
    metric_id: str
    dimension: QualityDimension
    name: str
    value: float
    max_value: float = 100.0
    unit: str = "%"
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class QualityScore(BaseModel):
    """Overall quality score for a dataset"""
    dataset_id: str
    dataset_name: str
    timestamp: datetime
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    total_records: int
    metrics: List[QualityMetric]
    passed_rules: int
    failed_rules: int
    warnings: int


class Alert(BaseModel):
    """Data quality alert"""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    rule_id: str
    rule_name: str
    dimension: QualityDimension
    message: str
    dataset_id: str
    metric_value: float
    threshold: float
    details: Dict[str, Any] = Field(default_factory=dict)
    acknowledged: bool = False


class DatasetProfile(BaseModel):
    """Statistical profile of a dataset"""
    dataset_id: str
    dataset_name: str
    total_records: int
    total_columns: int
    timestamp: datetime
    column_profiles: Dict[str, Dict[str, Any]]
    duplicate_count: int
    duplicate_percentage: float


class DuplicateRecord(BaseModel):
    """Information about duplicate records"""
    group_id: str
    records: List[Dict[str, Any]]
    match_score: float
    match_method: str  # 'exact' or 'fuzzy'
    matching_columns: List[str]


class ValidationResult(BaseModel):
    """Result of a validation check"""
    passed: bool
    score: float
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    affected_records: int = 0


class DataQualityReport(BaseModel):
    """Comprehensive data quality report"""
    report_id: str
    dataset_id: str
    dataset_name: str
    generated_at: datetime
    quality_score: QualityScore
    profile: DatasetProfile
    duplicates: List[DuplicateRecord]
    alerts: List[Alert]
    recommendations: List[str]
    trend_data: Optional[Dict[str, Any]] = None
