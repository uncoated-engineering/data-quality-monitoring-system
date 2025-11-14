import { useState } from 'react';
import { datasetAPI } from '../services/api';
import type { QualityMetric } from '../types';

interface MetricDetailsProps {
  metric: QualityMetric;
  datasetId: string;
}

function MetricDetails({ metric, datasetId }: MetricDetailsProps) {
  const [expanded, setExpanded] = useState(false);
  const [problematicData, setProblematicData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const getMetricType = (metric: QualityMetric): 'duplicates' | 'missing' | 'outliers' | null => {
    const name = metric.name.toLowerCase();
    if (name.includes('uniqueness') || name.includes('duplicate')) {
      return 'duplicates';
    } else if (name.includes('completeness') || name.includes('missing')) {
      return 'missing';
    } else if (name.includes('accuracy') || name.includes('outlier')) {
      return 'outliers';
    }
    return null;
  };

  const loadProblematicRecords = async () => {
    const metricType = getMetricType(metric);
    if (!metricType) return;

    setLoading(true);
    try {
      // Extract column information from details if available
      let column: string | undefined;

      // For column-specific metrics
      if (metric.details?.by_column) {
        // Find the worst column
        const columns = Object.entries(metric.details.by_column) as [string, number][];
        const worstColumn = columns.reduce((prev, curr) =>
          curr[1] < prev[1] ? curr : prev
        );
        column = worstColumn[0];
      }

      const data = await datasetAPI.getProblematicRecords(datasetId, metricType, column);
      setProblematicData(data);
    } catch (err) {
      console.error('Failed to load problematic records', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExpand = () => {
    if (!expanded) {
      loadProblematicRecords();
    }
    setExpanded(!expanded);
  };

  const getStatusClass = (value: number) => {
    if (value >= 90) return 'badge-success';
    if (value >= 70) return 'badge-info';
    if (value >= 50) return 'badge-warning';
    return 'badge-danger';
  };

  const getStatusLabel = (value: number) => {
    if (value >= 90) return 'Excellent';
    if (value >= 70) return 'Good';
    if (value >= 50) return 'Fair';
    return 'Poor';
  };

  const hasProblematicRecords = getMetricType(metric) !== null && metric.value < 100;

  return (
    <div style={{ marginBottom: '0.5rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.75rem',
          borderRadius: '0.375rem',
          backgroundColor: expanded ? '#f0f9ff' : 'transparent',
          cursor: hasProblematicRecords ? 'pointer' : 'default',
          transition: 'background-color 0.2s'
        }}
        onClick={hasProblematicRecords ? handleExpand : undefined}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 500 }}>{metric.name}</div>
          {metric.details?.by_column && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {Object.keys(metric.details.by_column).length} columns analyzed
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ fontWeight: 600, fontSize: '1.125rem' }}>
            {metric.value.toFixed(2)}{metric.unit}
          </div>
          <span className={`badge ${getStatusClass(metric.value)}`}>
            {getStatusLabel(metric.value)}
          </span>
          {hasProblematicRecords && (
            <button
              style={{
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontSize: '1.25rem',
                color: 'var(--primary-color)',
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s'
              }}
            >
              ▼
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          backgroundColor: '#f9fafb',
          borderRadius: '0.375rem',
          border: '1px solid var(--border-color)'
        }}>
          {loading ? (
            <div className="loading"><div className="spinner"></div></div>
          ) : problematicData ? (
            <div>
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                  {problematicData.explanation}
                </div>

                {/* Show column-level details */}
                {metric.details?.by_column && (
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>Column Breakdown:</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.5rem' }}>
                      {Object.entries(metric.details.by_column)
                        .sort(([, a], [, b]) => (a as number) - (b as number))
                        .slice(0, 10)
                        .map(([col, val]) => (
                          <div key={col} style={{
                            padding: '0.5rem',
                            backgroundColor: 'white',
                            borderRadius: '0.25rem',
                            border: '1px solid var(--border-color)'
                          }}>
                            <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{col}</div>
                            <div style={{ fontSize: '1rem', color: (val as number) < 90 ? 'var(--warning-color)' : 'var(--success-color)' }}>
                              {(val as number).toFixed(2)}%
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Show problematic records */}
                {problematicData.records && problematicData.records.length > 0 && (
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: '0.5rem' }}>
                      Sample Problematic Records (showing {Math.min(5, problematicData.records.length)} of {problematicData.count}):
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                      <table className="table" style={{ fontSize: '0.875rem' }}>
                        <thead>
                          <tr>
                            {Object.keys(problematicData.records[0]).map((key: string) => (
                              <th key={key} style={{ minWidth: '100px' }}>{key}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {problematicData.records.slice(0, 5).map((record: any, idx: number) => (
                            <tr key={idx}>
                              {Object.entries(record).map(([key, value], cellIdx) => {
                                const displayValue = value === null || value === undefined
                                  ? <span style={{ color: 'var(--danger-color)', fontStyle: 'italic' }}>null</span>
                                  : String(value);

                                return (
                                  <td key={cellIdx} style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {displayValue}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div>No details available</div>
          )}
        </div>
      )}
    </div>
  );
}

export default MetricDetails;
