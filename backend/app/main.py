"""
Data Quality Monitoring System - Main API
FastAPI application for data quality monitoring and alerting
"""
import io
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np

from app.models.data_quality import (
    QualityScore, QualityRule, Alert, AlertSeverity,
    QualityDimension, DatasetProfile, DuplicateRecord,
    DataQualityReport
)
from app.core.quality_engine import DataQualityEngine
from app.core.deduplication import DeduplicationEngine
from app.services.profiler import DataProfiler
from app.services.alerting import AlertingService
from app.services.monitoring import MonitoringService

# Initialize FastAPI app
app = FastAPI(
    title="Data Quality Monitoring System",
    description="Automated data quality monitoring with alerting and visualization",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
quality_engine = DataQualityEngine()
dedup_engine = DeduplicationEngine()
profiler = DataProfiler()
alerting_service = AlertingService()
monitoring_service = MonitoringService()

# In-memory storage for datasets (in production, use proper database)
datasets = {}


# Request/Response Models
class AssessmentRequest(BaseModel):
    dataset_id: str
    rules: Optional[List[QualityRule]] = None


class DeduplicationRequest(BaseModel):
    dataset_id: str
    key_columns: Optional[List[str]] = None
    fuzzy_columns: Optional[List[str]] = None
    methods: List[str] = ["exact"]


class RuleCreateRequest(BaseModel):
    name: str
    dimension: QualityDimension
    description: str
    threshold: float
    column: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True


# Health check
@app.get("/")
async def root():
    return {
        "service": "Data Quality Monitoring System",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "datasets_loaded": len(datasets),
        "active_alerts": len(alerting_service.get_active_alerts())
    }


# Dataset Management
@app.post("/api/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_id: Optional[str] = None,
    dataset_name: Optional[str] = None
):
    """Upload a dataset for quality monitoring"""
    try:
        # Read file
        contents = await file.read()

        # Determine file type and read accordingly
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        elif file.filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Generate dataset ID if not provided
        if not dataset_id:
            dataset_id = str(uuid.uuid4())

        if not dataset_name:
            dataset_name = file.filename

        # Store dataset
        datasets[dataset_id] = {
            "id": dataset_id,
            "name": dataset_name,
            "dataframe": df,
            "uploaded_at": datetime.now().isoformat(),
            "rows": len(df),
            "columns": len(df.columns)
        }

        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading dataset: {str(e)}")


@app.get("/api/datasets")
async def list_datasets():
    """List all uploaded datasets"""
    return [
        {
            "dataset_id": ds["id"],
            "dataset_name": ds["name"],
            "uploaded_at": ds["uploaded_at"],
            "rows": ds["rows"],
            "columns": ds["columns"]
        }
        for ds in datasets.values()
    ]


@app.get("/api/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get information about a specific dataset"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    return {
        "dataset_id": ds["id"],
        "dataset_name": ds["name"],
        "uploaded_at": ds["uploaded_at"],
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_data": df.head(5).to_dict('records')
    }


@app.get("/api/datasets/{dataset_id}/sample")
async def get_dataset_sample(
    dataset_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get sample data from a dataset with pagination"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    # Get sample with pagination
    sample = df.iloc[offset:offset+limit]

    return {
        "dataset_id": dataset_id,
        "total_rows": len(df),
        "offset": offset,
        "limit": limit,
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "data": sample.to_dict('records')
    }


@app.get("/api/datasets/{dataset_id}/problematic")
async def get_problematic_records(
    dataset_id: str,
    metric_type: str = Query(..., description="Type of issue: duplicates, missing, outliers"),
    column: Optional[str] = None
):
    """Get problematic records for a specific metric"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    problematic_records = []
    explanation = ""

    if metric_type == "duplicates":
        # Find duplicate rows
        if column:
            duplicated_mask = df.duplicated(subset=[column], keep=False)
        else:
            duplicated_mask = df.duplicated(keep=False)

        problematic_df = df[duplicated_mask]
        problematic_records = problematic_df.replace({np.nan: None}).to_dict('records')
        explanation = f"Found {len(problematic_df)} duplicate records"

        if column:
            explanation += f" in column '{column}'"

    elif metric_type == "missing":
        # Find rows with missing values
        if column:
            missing_mask = df[column].isnull()
            problematic_df = df[missing_mask]
            explanation = f"Found {len(problematic_df)} records with missing values in '{column}'"
        else:
            missing_mask = df.isnull().any(axis=1)
            problematic_df = df[missing_mask]
            explanation = f"Found {len(problematic_df)} records with missing values"

        problematic_records = problematic_df.replace({np.nan: None}).to_dict('records')

    elif metric_type == "outliers":
        # Find outliers using IQR method
        if column and column in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            outlier_mask = (df[column] < (Q1 - 1.5 * IQR)) | (df[column] > (Q3 + 1.5 * IQR))
            problematic_df = df[outlier_mask]
            problematic_records = problematic_df.replace({np.nan: None}).to_dict('records')
            explanation = f"Found {len(problematic_df)} outlier records in '{column}'"
        else:
            explanation = "No numeric column specified for outlier detection"

    return {
        "dataset_id": dataset_id,
        "metric_type": metric_type,
        "column": column,
        "count": len(problematic_records),
        "explanation": explanation,
        "records": problematic_records[:100]  # Limit to 100 records
    }


# Quality Assessment
@app.post("/api/assess/{dataset_id}", response_model=QualityScore)
async def assess_quality(dataset_id: str, request: Optional[AssessmentRequest] = None):
    """Perform quality assessment on a dataset"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    # Perform assessment
    rules = request.rules if request else []
    quality_score = quality_engine.assess_quality(
        df,
        dataset_id=dataset_id,
        dataset_name=ds["name"],
        rules=rules
    )

    # Store alerts
    for alert in quality_engine.get_alerts():
        alert.dataset_id = dataset_id
        alerting_service.add_alert(alert)

    # Record score in monitoring
    monitoring_service.record_quality_score(quality_score)

    return quality_score


@app.get("/api/assess/{dataset_id}/history")
async def get_quality_history(
    dataset_id: str,
    days: int = Query(30, ge=1, le=365)
):
    """Get quality score history for a dataset"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    history = monitoring_service.get_quality_history(dataset_id, days)
    return {
        "dataset_id": dataset_id,
        "days": days,
        "history": history
    }


@app.get("/api/assess/{dataset_id}/trends")
async def get_quality_trends(
    dataset_id: str,
    days: int = Query(7, ge=1, le=90)
):
    """Get quality trend analysis"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    trends = monitoring_service.get_trend_analysis(dataset_id, days)
    return trends


# Data Profiling
@app.get("/api/profile/{dataset_id}", response_model=DatasetProfile)
async def profile_dataset(dataset_id: str):
    """Generate comprehensive profile of a dataset"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    profile = profiler.profile_dataset(df, dataset_id, ds["name"])
    return profile


# Deduplication
@app.post("/api/deduplication/{dataset_id}")
async def find_duplicates(dataset_id: str, request: DeduplicationRequest):
    """Find duplicate records in a dataset"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    # Find duplicates
    duplicates = dedup_engine.find_duplicates(
        df,
        key_columns=request.key_columns,
        fuzzy_columns=request.fuzzy_columns,
        methods=request.methods
    )

    stats = dedup_engine.get_deduplication_stats()

    return {
        "dataset_id": dataset_id,
        "duplicates": duplicates,
        "statistics": stats
    }


@app.post("/api/deduplication/{dataset_id}/merge")
async def merge_duplicates(
    dataset_id: str,
    strategy: str = Query("first", regex="^(first|last|best)$")
):
    """Merge duplicate records using specified strategy"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    # First find duplicates
    dedup_engine.find_duplicates(df, methods=['exact'])

    # Merge them
    merged_df = dedup_engine.merge_duplicates(df, strategy)

    # Update dataset
    datasets[dataset_id]["dataframe"] = merged_df
    datasets[dataset_id]["rows"] = len(merged_df)

    return {
        "dataset_id": dataset_id,
        "original_rows": len(df),
        "merged_rows": len(merged_df),
        "removed_duplicates": len(df) - len(merged_df),
        "strategy": strategy
    }


# Alerting
@app.get("/api/alerts", response_model=List[Alert])
async def get_alerts(
    severity: Optional[AlertSeverity] = None,
    dataset_id: Optional[str] = None,
    active_only: bool = True
):
    """Get alerts with optional filtering"""
    if active_only:
        alerts = alerting_service.get_active_alerts(severity, dataset_id)
    else:
        alerts = alerting_service.alerts

    return alerts


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    success = alerting_service.acknowledge_alert(alert_id)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"alert_id": alert_id, "acknowledged": True}


@app.get("/api/alerts/summary")
async def get_alert_summary():
    """Get alert summary statistics"""
    summary = alerting_service.get_alert_summary()
    return summary


@app.get("/api/alerts/trends")
async def get_alert_trends(days: int = Query(7, ge=1, le=90)):
    """Get alert trend analysis"""
    trends = alerting_service.get_alert_trends(days)
    return trends


# Reports
@app.get("/api/reports/{dataset_id}", response_model=DataQualityReport)
async def generate_report(dataset_id: str):
    """Generate comprehensive data quality report"""
    if dataset_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ds = datasets[dataset_id]
    df = ds["dataframe"]

    # Perform all checks
    quality_score = quality_engine.assess_quality(df, dataset_id, ds["name"])
    profile = profiler.profile_dataset(df, dataset_id, ds["name"])
    duplicates = dedup_engine.find_duplicates(df, methods=['exact'])

    # Get alerts for this dataset
    dataset_alerts = [a for a in alerting_service.alerts if a.dataset_id == dataset_id]

    # Generate recommendations
    recommendations = alerting_service.generate_recommendations(
        quality_score,
        dataset_alerts
    )

    # Get trend data
    trend_data = monitoring_service.get_trend_analysis(dataset_id, days=7)

    report = DataQualityReport(
        report_id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        dataset_name=ds["name"],
        generated_at=datetime.now(),
        quality_score=quality_score,
        profile=profile,
        duplicates=duplicates,
        alerts=dataset_alerts[:10],  # Top 10 alerts
        recommendations=recommendations,
        trend_data=trend_data
    )

    return report


# Monitoring
@app.get("/api/monitoring/datasets")
async def get_monitored_datasets():
    """Get list of all monitored datasets"""
    datasets_list = monitoring_service.get_all_datasets()
    return datasets_list


@app.get("/api/monitoring/{dataset_id}/stats")
async def get_dataset_statistics(dataset_id: str):
    """Get statistical summary for a dataset"""
    stats = monitoring_service.get_dataset_statistics(dataset_id)

    if not stats:
        raise HTTPException(status_code=404, detail="No monitoring data found for dataset")

    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
