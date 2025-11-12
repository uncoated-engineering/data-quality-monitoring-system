"""
Alerting Service
Manages quality alerts and notifications
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import numpy as np

from app.models.data_quality import (
    Alert, AlertSeverity, QualityScore, QualityRule, QualityDimension
)


class AlertingService:
    """
    Manages data quality alerts and notifications
    Implements alert aggregation, deduplication, and trending
    """

    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []

    def add_alert(self, alert: Alert) -> None:
        """Add a new alert"""
        self.alerts.append(alert)
        self.alert_history.append(alert)

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None,
                         dataset_id: Optional[str] = None) -> List[Alert]:
        """
        Get active (unacknowledged) alerts

        Args:
            severity: Filter by severity level
            dataset_id: Filter by dataset

        Returns:
            List of matching alerts
        """
        filtered = [a for a in self.alerts if not a.acknowledged]

        if severity:
            filtered = [a for a in filtered if a.severity == severity]

        if dataset_id:
            filtered = [a for a in filtered if a.dataset_id == dataset_id]

        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary statistics of alerts"""
        active_alerts = [a for a in self.alerts if not a.acknowledged]

        severity_counts = defaultdict(int)
        dimension_counts = defaultdict(int)

        for alert in active_alerts:
            severity_counts[alert.severity] += 1
            dimension_counts[alert.dimension] += 1

        return {
            "total_active": len(active_alerts),
            "by_severity": {
                "critical": severity_counts.get(AlertSeverity.CRITICAL, 0),
                "warning": severity_counts.get(AlertSeverity.WARNING, 0),
                "info": severity_counts.get(AlertSeverity.INFO, 0)
            },
            "by_dimension": dict(dimension_counts),
            "oldest_alert": min([a.timestamp for a in active_alerts]) if active_alerts else None,
            "newest_alert": max([a.timestamp for a in active_alerts]) if active_alerts else None
        }

    def get_alert_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze alert trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_alerts = [a for a in self.alert_history if a.timestamp >= cutoff_date]

        # Group by day
        daily_counts = defaultdict(lambda: defaultdict(int))

        for alert in recent_alerts:
            day = alert.timestamp.date().isoformat()
            daily_counts[day]["total"] += 1
            daily_counts[day][alert.severity] += 1

        # Calculate trend
        dates = sorted(daily_counts.keys())
        if len(dates) >= 2:
            recent_avg = np.mean([daily_counts[d]["total"] for d in dates[-3:]])
            earlier_avg = np.mean([daily_counts[d]["total"] for d in dates[:3]])
            trend = "increasing" if recent_avg > earlier_avg else "decreasing"
        else:
            trend = "stable"

        return {
            "period_days": days,
            "total_alerts": len(recent_alerts),
            "daily_breakdown": dict(daily_counts),
            "trend": trend,
            "dates": dates
        }

    def generate_recommendations(self, quality_score: QualityScore,
                                alerts: List[Alert]) -> List[str]:
        """
        Generate actionable recommendations based on quality issues

        Args:
            quality_score: Current quality score
            alerts: Active alerts

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze dimension scores
        for dimension, score in quality_score.dimension_scores.items():
            if score < 70:
                recommendations.extend(
                    self._get_dimension_recommendations(dimension, score)
                )

        # Analyze alert patterns
        severity_counts = defaultdict(int)
        for alert in alerts:
            severity_counts[alert.severity] += 1

        if severity_counts[AlertSeverity.CRITICAL] > 0:
            recommendations.append(
                f"Address {severity_counts[AlertSeverity.CRITICAL]} critical "
                "issues immediately to prevent data quality degradation"
            )

        # Deduplication recommendation
        if quality_score.dimension_scores.get(QualityDimension.UNIQUENESS, 100) < 95:
            recommendations.append(
                "Consider implementing automated deduplication processes "
                "to improve data uniqueness"
            )

        # Completeness recommendation
        if quality_score.dimension_scores.get(QualityDimension.COMPLETENESS, 100) < 80:
            recommendations.append(
                "Implement mandatory field validation at data entry points "
                "to improve completeness"
            )

        return recommendations[:10]  # Return top 10 recommendations

    def _get_dimension_recommendations(self, dimension: QualityDimension,
                                      score: float) -> List[str]:
        """Get specific recommendations for a dimension"""
        recommendations_map = {
            QualityDimension.COMPLETENESS: [
                "Add validation rules to require critical fields",
                "Investigate data collection processes for missing data",
                "Implement default value strategies where appropriate"
            ],
            QualityDimension.ACCURACY: [
                "Review and update data type constraints",
                "Implement input validation with appropriate formats",
                "Establish data quality rules for acceptable ranges"
            ],
            QualityDimension.CONSISTENCY: [
                "Standardize data formats across all sources",
                "Implement reference data management",
                "Create data quality rules for cross-field validation"
            ],
            QualityDimension.UNIQUENESS: [
                "Enable duplicate detection at data entry",
                "Implement master data management processes",
                "Review and merge duplicate records"
            ],
            QualityDimension.VALIDITY: [
                "Update business rule validations",
                "Implement lookup tables for valid values",
                "Review and correct invalid data records"
            ]
        }

        return recommendations_map.get(dimension, [])

    def clear_old_alerts(self, days: int = 30) -> int:
        """
        Clear acknowledged alerts older than specified days

        Args:
            days: Number of days to retain

        Returns:
            Number of alerts cleared
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        initial_count = len(self.alerts)

        self.alerts = [
            a for a in self.alerts
            if not a.acknowledged or a.timestamp >= cutoff_date
        ]

        return initial_count - len(self.alerts)
