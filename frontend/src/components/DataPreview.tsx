import { useState, useEffect } from 'react';
import { datasetAPI } from '../services/api';

interface DataPreviewProps {
  datasetId: string;
}

function DataPreview({ datasetId }: DataPreviewProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [datasetId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await datasetAPI.getSample(datasetId, 10, 0);
      setData(response);
    } catch (err) {
      setError('Failed to load data preview');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  if (error) {
    return <div className="alert alert-critical">{error}</div>;
  }

  if (!data || !data.data || data.data.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
      No data available
    </div>;
  }

  const columns = data.columns || [];
  const rows = data.data || [];

  return (
    <div>
      <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
        Showing {rows.length} of {data.total_rows} records
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ minWidth: '50px', textAlign: 'center' }}>#</th>
              {columns.map((col: string) => (
                <th key={col} style={{ minWidth: '120px' }}>
                  {col}
                  <div style={{ fontSize: '0.75rem', opacity: 0.7, fontWeight: 'normal' }}>
                    {data.dtypes[col]}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row: any, index: number) => (
              <tr key={index}>
                <td style={{ textAlign: 'center', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  {index + 1}
                </td>
                {columns.map((col: string) => {
                  const value = row[col];
                  const displayValue = value === null || value === undefined
                    ? <span style={{ color: 'var(--danger-color)', fontStyle: 'italic' }}>null</span>
                    : String(value);

                  return (
                    <td key={col} style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
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
  );
}

export default DataPreview;
