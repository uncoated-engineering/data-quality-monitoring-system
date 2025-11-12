"""
Simple test script to verify the Data Quality Monitoring System
"""
import pandas as pd
from app.core.quality_engine import DataQualityEngine
from app.core.deduplication import DeduplicationEngine
from app.services.profiler import DataProfiler
from app.services.alerting import AlertingService
from app.models.data_quality import QualityRule, QualityDimension, AlertSeverity


def test_quality_engine():
    """Test the quality engine with sample data"""
    print("Testing Quality Engine...")

    # Create sample data with quality issues
    data = {
        'customer_id': [1, 2, 3, 4, 5, None, 7, 8, 9, 10],
        'name': ['John', 'Jane', 'Bob', 'Alice', 'John', 'Mary', 'Tom', 'Sue', 'Bill', 'Ann'],
        'email': ['john@test.com', 'jane@test.com', None, 'alice@test.com', 'john@test.com',
                 'mary@test.com', 'tom@test.com', 'sue@test.com', 'bill@test.com', 'ann@test.com'],
        'balance': [1000, 2000, 3000, -100, 1000, 5000, 6000, 7000, 8000, 9000],
        'created_date': ['2023-01-01'] * 10
    }

    df = pd.DataFrame(data)

    engine = DataQualityEngine()
    score = engine.assess_quality(df, 'test-001', 'Test Dataset')

    print(f"✓ Overall Score: {score.overall_score}%")
    print(f"✓ Total Records: {score.total_records}")
    print(f"✓ Dimension Scores:")
    for dimension, value in score.dimension_scores.items():
        print(f"  - {dimension}: {value}%")

    assert score.overall_score > 0, "Quality score should be positive"
    assert len(score.metrics) > 0, "Should have metrics"

    print("Quality Engine: PASSED\n")


def test_deduplication():
    """Test the deduplication engine"""
    print("Testing Deduplication Engine...")

    data = {
        'name': ['John Smith', 'John Smith', 'Jane Doe', 'Jane D.', 'Bob Jones'],
        'email': ['john@test.com', 'john@test.com', 'jane@test.com', 'jane@test.com', 'bob@test.com']
    }

    df = pd.DataFrame(data)

    dedup = DeduplicationEngine(fuzzy_threshold=85)

    # Test exact matching
    duplicates = dedup.find_duplicates(df, methods=['exact'])
    print(f"✓ Found {len(duplicates)} duplicate groups (exact matching)")

    # Test fuzzy matching
    duplicates_fuzzy = dedup.find_duplicates(df, fuzzy_columns=['name'], methods=['fuzzy'])
    print(f"✓ Found {len(duplicates_fuzzy)} duplicate groups (fuzzy matching)")

    # Test deduplication stats
    stats = dedup.get_deduplication_stats()
    print(f"✓ Deduplication stats: {stats}")

    assert len(duplicates) > 0, "Should find exact duplicates"

    print("Deduplication Engine: PASSED\n")


def test_profiler():
    """Test the data profiler"""
    print("Testing Data Profiler...")

    data = {
        'id': range(100),
        'value': [i * 10 for i in range(100)],
        'category': ['A'] * 50 + ['B'] * 50,
        'description': [f'Item {i}' for i in range(100)]
    }

    df = pd.DataFrame(data)

    profiler = DataProfiler()
    profile = profiler.profile_dataset(df, 'test-001', 'Test Dataset')

    print(f"✓ Profiled {profile.total_records} records")
    print(f"✓ {profile.total_columns} columns")
    print(f"✓ {len(profile.column_profiles)} column profiles generated")

    assert profile.total_records == 100, "Should have 100 records"
    assert profile.total_columns == 4, "Should have 4 columns"
    assert len(profile.column_profiles) == 4, "Should have 4 column profiles"

    print("Data Profiler: PASSED\n")


def test_alerting():
    """Test the alerting service"""
    print("Testing Alerting Service...")

    from app.models.data_quality import Alert
    from datetime import datetime
    import uuid

    alerting = AlertingService()

    # Create test alert
    alert = Alert(
        alert_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        severity=AlertSeverity.WARNING,
        rule_id='rule-001',
        rule_name='Test Rule',
        dimension=QualityDimension.COMPLETENESS,
        message='Test alert message',
        dataset_id='test-001',
        metric_value=75.0,
        threshold=80.0,
        details={}
    )

    alerting.add_alert(alert)

    # Get active alerts
    active = alerting.get_active_alerts()
    print(f"✓ {len(active)} active alerts")

    # Get summary
    summary = alerting.get_alert_summary()
    print(f"✓ Alert summary: {summary['total_active']} total")

    assert len(active) == 1, "Should have 1 active alert"
    assert summary['total_active'] == 1, "Summary should show 1 alert"

    print("Alerting Service: PASSED\n")


def main():
    """Run all tests"""
    print("="*50)
    print("Data Quality Monitoring System - Test Suite")
    print("="*50 + "\n")

    try:
        test_quality_engine()
        test_deduplication()
        test_profiler()
        test_alerting()

        print("="*50)
        print("ALL TESTS PASSED ✓")
        print("="*50)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
