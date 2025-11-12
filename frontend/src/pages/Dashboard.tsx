import { useState, useEffect } from 'react';
import { qualityAPI, alertAPI, profileAPI } from '../services/api';
import type { QualityScore, Alert, DatasetProfile, QualityHistory, TrendAnalysis } from '../types';
import QualityScoreCard from '../components/QualityScoreCard';
import TrendChart from '../components/TrendChart';
import DimensionScores from '../components/DimensionScores';
import AlertsList from '../components/AlertsList';

interface DashboardProps {
  datasetId: string | null;
}

function Dashboard({ datasetId }: DashboardProps) {
  const [qualityScore, setQualityScore] = useState<QualityScore | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<QualityHistory[]>([]);
  const [trends, setTrends] = useState<TrendAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (datasetId) {
      loadDashboardData();
    }
  }, [datasetId]);

  const loadDashboardData = async () => {
    if (!datasetId) return;

    setLoading(true);
    setError(null);

    try {
      // Run assessment
      const score = await qualityAPI.assessQuality(datasetId);
      setQualityScore(score);

      // Load profile
      const prof = await profileAPI.profileDataset(datasetId);
      setProfile(prof);

      // Load alerts for this dataset
      const alertsData = await alertAPI.getAlerts({
        dataset_id: datasetId,
        active_only: true
      });
      setAlerts(alertsData);

      // Load history
      const historyData = await qualityAPI.getQualityHistory(datasetId, 30);
      setHistory(historyData);

      // Load trends
      const trendsData = await qualityAPI.getQualityTrends(datasetId, 7);
      setTrends(trendsData);

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!datasetId) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>Welcome to Data Quality Monitoring</h2>
          <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
            Upload a dataset or select an existing one to begin monitoring
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-critical">
        {error}
      </div>
    );
  }

  if (!qualityScore) {
    return null;
  }

  return (
    <div>
      <div className="card-header" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h2 className="card-title">{qualityScore.dataset_name}</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            {qualityScore.total_records.toLocaleString()} records assessed
          </p>
        </div>
        <button className="btn btn-primary" onClick={loadDashboardData}>
          Refresh Assessment
        </button>
      </div>

      {/* Quality Score Overview */}
      <div className="grid grid-cols-3">
        <QualityScoreCard
          score={qualityScore.overall_score}
          label="Overall Quality Score"
          trend={trends}
        />

        <div className="stat-card">
          <div className="stat-label">Passed Rules</div>
          <div className="stat-value" style={{ color: 'var(--success-color)' }}>
            {qualityScore.passed_rules}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Failed Rules / Warnings</div>
          <div className="stat-value" style={{ color: 'var(--danger-color)' }}>
            {qualityScore.failed_rules} / {qualityScore.warnings}
          </div>
        </div>
      </div>

      {/* Dimension Scores */}
      <div className="card">
        <h3 className="card-title">Quality Dimensions</h3>
        <DimensionScores scores={qualityScore.dimension_scores} />
      </div>

      {/* Trend Chart */}
      {history.length > 0 && (
        <div className="card">
          <h3 className="card-title">Quality Trend (Last 30 Days)</h3>
          <TrendChart data={history} />
        </div>
      )}

      {/* Data Profile */}
      {profile && (
        <div className="grid grid-cols-2">
          <div className="card">
            <h3 className="card-title">Dataset Statistics</h3>
            <div style={{ marginTop: '1rem' }}>
              <div style={{ marginBottom: '1rem' }}>
                <div className="stat-label">Total Records</div>
                <div className="stat-value" style={{ fontSize: '1.5rem' }}>
                  {profile.total_records.toLocaleString()}
                </div>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <div className="stat-label">Total Columns</div>
                <div className="stat-value" style={{ fontSize: '1.5rem' }}>
                  {profile.total_columns}
                </div>
              </div>
              <div>
                <div className="stat-label">Duplicate Records</div>
                <div className="stat-value" style={{ fontSize: '1.5rem', color: profile.duplicate_percentage > 5 ? 'var(--warning-color)' : 'var(--success-color)' }}>
                  {profile.duplicate_count} ({profile.duplicate_percentage.toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Active Alerts</h3>
            {alerts.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No active alerts
              </div>
            ) : (
              <AlertsList alerts={alerts.slice(0, 5)} />
            )}
          </div>
        </div>
      )}

      {/* Metrics Details */}
      <div className="card">
        <h3 className="card-title">Metrics Details</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Dimension</th>
              <th>Metric</th>
              <th>Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {qualityScore.metrics.map((metric) => (
              <tr key={metric.metric_id}>
                <td>
                  <span className="badge badge-info" style={{ textTransform: 'capitalize' }}>
                    {metric.dimension}
                  </span>
                </td>
                <td>{metric.name}</td>
                <td>
                  {metric.value.toFixed(2)}{metric.unit}
                </td>
                <td>
                  {metric.value >= 90 ? (
                    <span className="badge badge-success">Excellent</span>
                  ) : metric.value >= 70 ? (
                    <span className="badge badge-info">Good</span>
                  ) : metric.value >= 50 ? (
                    <span className="badge badge-warning">Fair</span>
                  ) : (
                    <span className="badge badge-danger">Poor</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Dashboard;
