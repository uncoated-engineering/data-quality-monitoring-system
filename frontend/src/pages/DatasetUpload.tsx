import { useState } from 'react';
import { datasetAPI } from '../services/api';

interface DatasetUploadProps {
  onUploadSuccess: (datasetId: string) => void;
}

function DatasetUpload({ onUploadSuccess }: DatasetUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    if (!datasetName) {
      setDatasetName(selectedFile.name);
    }
    setError(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await datasetAPI.uploadDataset(file, datasetName);
      onUploadSuccess(result.dataset_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload dataset');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">Upload Dataset</h2>

      <div style={{ marginTop: '2rem' }}>
        <div
          className={`upload-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
            style={{ display: 'none' }}
          />

          {file ? (
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                {file.name}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                {(file.size / 1024).toFixed(2)} KB
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Drop your file here or click to browse
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                Supported formats: CSV, Excel, JSON
              </div>
            </div>
          )}
        </div>

        {file && (
          <div style={{ marginTop: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
              Dataset Name (optional)
            </label>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="Enter dataset name"
              style={{
                width: '100%',
                padding: '0.625rem',
                border: '1px solid var(--border-color)',
                borderRadius: '0.375rem',
                fontSize: '1rem'
              }}
            />
          </div>
        )}

        {error && (
          <div className="alert alert-critical" style={{ marginTop: '1rem' }}>
            {error}
          </div>
        )}

        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!file || uploading}
            style={{ opacity: !file || uploading ? 0.5 : 1 }}
          >
            {uploading ? 'Uploading...' : 'Upload and Assess'}
          </button>

          {file && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setFile(null);
                setDatasetName('');
                setError(null);
              }}
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default DatasetUpload;
