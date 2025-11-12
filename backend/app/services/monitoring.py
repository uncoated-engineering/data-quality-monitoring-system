"""
Monitoring Service
Tracks data quality metrics over time
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import sqlite3
from pathlib import Path

from app.models.data_quality import QualityScore, QualityDimension


class MonitoringService:
    """
    Tracks and stores quality metrics over time
    Provides trend analysis and historical data
    """

    def __init__(self, db_path: str = "data/quality_metrics.db"):
        """Initialize monitoring service with SQLite database"""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Quality scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                overall_score REAL NOT NULL,
                total_records INTEGER NOT NULL,
                passed_rules INTEGER NOT NULL,
                failed_rules INTEGER NOT NULL,
                warnings INTEGER NOT NULL,
                dimension_scores TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Dimension metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dimension_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                dimension TEXT NOT NULL,
                score REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dataset_timestamp
            ON quality_scores(dataset_id, timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dimension_dataset
            ON dimension_metrics(dataset_id, dimension, timestamp)
        """)

        conn.commit()
        conn.close()

    def record_quality_score(self, quality_score: QualityScore) -> None:
        """Store quality score in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store overall score
        cursor.execute("""
            INSERT INTO quality_scores
            (dataset_id, dataset_name, timestamp, overall_score, total_records,
             passed_rules, failed_rules, warnings, dimension_scores)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quality_score.dataset_id,
            quality_score.dataset_name,
            quality_score.timestamp.isoformat(),
            quality_score.overall_score,
            quality_score.total_records,
            quality_score.passed_rules,
            quality_score.failed_rules,
            quality_score.warnings,
            json.dumps({k.value: v for k, v in quality_score.dimension_scores.items()})
        ))

        # Store dimension scores
        for dimension, score in quality_score.dimension_scores.items():
            cursor.execute("""
                INSERT INTO dimension_metrics
                (dataset_id, timestamp, dimension, score)
                VALUES (?, ?, ?, ?)
            """, (
                quality_score.dataset_id,
                quality_score.timestamp.isoformat(),
                dimension.value,
                score
            ))

        conn.commit()
        conn.close()

    def get_quality_history(self, dataset_id: str,
                          days: int = 30) -> List[Dict[str, Any]]:
        """
        Get quality score history for a dataset

        Args:
            dataset_id: Dataset identifier
            days: Number of days of history to retrieve

        Returns:
            List of historical quality scores
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT timestamp, overall_score, total_records,
                   passed_rules, failed_rules, warnings, dimension_scores
            FROM quality_scores
            WHERE dataset_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (dataset_id, cutoff_date))

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "timestamp": row[0],
                "overall_score": row[1],
                "total_records": row[2],
                "passed_rules": row[3],
                "failed_rules": row[4],
                "warnings": row[5],
                "dimension_scores": json.loads(row[6])
            })

        return history

    def get_dimension_trend(self, dataset_id: str,
                          dimension: QualityDimension,
                          days: int = 30) -> List[Dict[str, Any]]:
        """
        Get trend data for a specific quality dimension

        Args:
            dataset_id: Dataset identifier
            dimension: Quality dimension
            days: Number of days of history

        Returns:
            List of timestamp/score pairs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT timestamp, score
            FROM dimension_metrics
            WHERE dataset_id = ? AND dimension = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (dataset_id, dimension.value, cutoff_date))

        rows = cursor.fetchall()
        conn.close()

        return [{"timestamp": row[0], "score": row[1]} for row in rows]

    def get_trend_analysis(self, dataset_id: str,
                          days: int = 7) -> Dict[str, Any]:
        """
        Analyze quality trends

        Args:
            dataset_id: Dataset identifier
            days: Number of days to analyze

        Returns:
            Trend analysis results
        """
        history = self.get_quality_history(dataset_id, days)

        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "change": 0,
                "current_score": history[0]["overall_score"] if history else 0,
                "previous_score": 0
            }

        current_score = history[-1]["overall_score"]
        previous_score = history[0]["overall_score"]
        change = current_score - previous_score

        # Calculate trend
        if change > 5:
            trend = "improving"
        elif change < -5:
            trend = "degrading"
        else:
            trend = "stable"

        # Dimension-level trends
        dimension_trends = {}
        for dimension in QualityDimension:
            dim_data = self.get_dimension_trend(dataset_id, dimension, days)
            if len(dim_data) >= 2:
                dim_change = dim_data[-1]["score"] - dim_data[0]["score"]
                dimension_trends[dimension.value] = {
                    "change": round(dim_change, 2),
                    "current": dim_data[-1]["score"],
                    "trend": "improving" if dim_change > 2 else "degrading" if dim_change < -2 else "stable"
                }

        return {
            "trend": trend,
            "change": round(change, 2),
            "current_score": current_score,
            "previous_score": previous_score,
            "dimension_trends": dimension_trends,
            "data_points": len(history)
        }

    def get_dataset_statistics(self, dataset_id: str) -> Dict[str, Any]:
        """Get overall statistics for a dataset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get latest score
        cursor.execute("""
            SELECT overall_score, timestamp, total_records
            FROM quality_scores
            WHERE dataset_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (dataset_id,))

        latest = cursor.fetchone()

        # Get average score
        cursor.execute("""
            SELECT AVG(overall_score), MIN(overall_score), MAX(overall_score), COUNT(*)
            FROM quality_scores
            WHERE dataset_id = ?
        """, (dataset_id,))

        stats = cursor.fetchone()

        conn.close()

        if not latest or not stats:
            return {}

        return {
            "latest_score": latest[0],
            "latest_timestamp": latest[1],
            "latest_record_count": latest[2],
            "average_score": round(stats[0], 2) if stats[0] else 0,
            "min_score": stats[1],
            "max_score": stats[2],
            "total_assessments": stats[3]
        }

    def get_all_datasets(self) -> List[Dict[str, Any]]:
        """Get list of all monitored datasets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT dataset_id, dataset_name,
                   MAX(timestamp) as last_assessed,
                   COUNT(*) as assessment_count
            FROM quality_scores
            GROUP BY dataset_id, dataset_name
            ORDER BY last_assessed DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "dataset_id": row[0],
                "dataset_name": row[1],
                "last_assessed": row[2],
                "assessment_count": row[3]
            }
            for row in rows
        ]
