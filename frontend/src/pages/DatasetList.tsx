import { useState, useEffect } from 'react';
import { datasetAPI } from '../services/api';
import type { Dataset } from '../types';

interface DatasetListProps {
  onSelectDataset: (datasetId: string) => void;
}

function DatasetList({ onSelectDataset }: DatasetListProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await datasetAPI.listDatasets();
      setDatasets(data);
    } catch (err) {
      setError('Failed to load datasets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Uploaded Datasets</h2>
        <button className="btn btn-primary" onClick={loadDatasets}>
          Refresh
        </button>
      </div>

      {datasets.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <p>No datasets uploaded yet</p>
          <p style={{ marginTop: '0.5rem' }}>Upload a dataset to get started</p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Dataset Name</th>
              <th>Uploaded</th>
              <th>Records</th>
              <th>Columns</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {datasets.map(dataset => (
              <tr key={dataset.dataset_id}>
                <td style={{ fontWeight: 500 }}>{dataset.dataset_name}</td>
                <td>{new Date(dataset.uploaded_at).toLocaleDateString()}</td>
                <td>{dataset.rows.toLocaleString()}</td>
                <td>{dataset.columns}</td>
                <td>
                  <button
                    className="btn btn-primary"
                    onClick={() => onSelectDataset(dataset.dataset_id)}
                  >
                    View Dashboard
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default DatasetList;
