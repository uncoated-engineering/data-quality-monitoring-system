import type { Alert } from '../types';

interface AlertsListProps {
  alerts: Alert[];
  onAcknowledge?: (alertId: string) => void;
}

function AlertsList({ alerts, onAcknowledge }: AlertsListProps) {
  if (alerts.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
        No alerts to display
      </div>
    );
  }

  return (
    <div>
      {alerts.map(alert => (
        <div key={alert.alert_id} className={`alert alert-${alert.severity}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                {alert.rule_name}
              </div>
              <div style={{ fontSize: '0.875rem' }}>
                {alert.message}
              </div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', opacity: 0.7 }}>
                {new Date(alert.timestamp).toLocaleString()}
              </div>
            </div>
            {onAcknowledge && !alert.acknowledged && (
              <button
                className="btn btn-secondary"
                onClick={() => onAcknowledge(alert.alert_id)}
                style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem' }}
              >
                Acknowledge
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default AlertsList;
