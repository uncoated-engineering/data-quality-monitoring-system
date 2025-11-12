import { useState, useEffect } from 'react';
import { alertAPI } from '../services/api';
import type { Alert } from '../types';
import AlertsList from '../components/AlertsList';

function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');

  useEffect(() => {
    loadAlerts();
    loadSummary();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const data = await alertAPI.getAlerts({ active_only: true });
      setAlerts(data);
    } catch (err) {
      console.error('Failed to load alerts', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await alertAPI.getAlertSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load summary', err);
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertAPI.acknowledgeAlert(alertId);
      await loadAlerts();
      await loadSummary();
    } catch (err) {
      console.error('Failed to acknowledge alert', err);
    }
  };

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter(a => a.severity === filter);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="card-title" style={{ marginBottom: '1.5rem' }}>Alerts Management</h2>

      {/* Alert Summary */}
      {summary && (
        <div className="grid grid-cols-4">
          <div className="stat-card">
            <div className="stat-label">Total Active</div>
            <div className="stat-value">{summary.total_active}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Critical</div>
            <div className="stat-value" style={{ color: 'var(--danger-color)' }}>
              {summary.by_severity.critical}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Warning</div>
            <div className="stat-value" style={{ color: 'var(--warning-color)' }}>
              {summary.by_severity.warning}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Info</div>
            <div className="stat-value" style={{ color: 'var(--primary-color)' }}>
              {summary.by_severity.info}
            </div>
          </div>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="card">
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <button
            className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter('all')}
          >
            All ({alerts.length})
          </button>
          <button
            className={`btn ${filter === 'critical' ? 'btn-danger' : 'btn-secondary'}`}
            onClick={() => setFilter('critical')}
          >
            Critical ({alerts.filter(a => a.severity === 'critical').length})
          </button>
          <button
            className={`btn ${filter === 'warning' ? 'btn-warning' : 'btn-secondary'}`}
            onClick={() => setFilter('warning')}
          >
            Warning ({alerts.filter(a => a.severity === 'warning').length})
          </button>
          <button
            className={`btn ${filter === 'info' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter('info')}
          >
            Info ({alerts.filter(a => a.severity === 'info').length})
          </button>
        </div>

        <AlertsList alerts={filteredAlerts} onAcknowledge={handleAcknowledge} />
      </div>
    </div>
  );
}

export default Alerts;
