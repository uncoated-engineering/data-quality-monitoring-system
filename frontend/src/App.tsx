import { useState } from 'react'
import './App.css'
import Dashboard from './pages/Dashboard'
import DatasetUpload from './pages/DatasetUpload'
import Alerts from './pages/Alerts'
import DatasetList from './pages/DatasetList'

type Page = 'dashboard' | 'datasets' | 'upload' | 'alerts';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard datasetId={selectedDatasetId} />;
      case 'datasets':
        return (
          <DatasetList
            onSelectDataset={(id) => {
              setSelectedDatasetId(id);
              setCurrentPage('dashboard');
            }}
          />
        );
      case 'upload':
        return (
          <DatasetUpload
            onUploadSuccess={(id) => {
              setSelectedDatasetId(id);
              setCurrentPage('dashboard');
            }}
          />
        );
      case 'alerts':
        return <Alerts />;
      default:
        return <Dashboard datasetId={selectedDatasetId} />;
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Data Quality Monitoring System</h1>
          <nav>
            <button
              className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => setCurrentPage('dashboard')}
            >
              Dashboard
            </button>
            <button
              className={`nav-link ${currentPage === 'datasets' ? 'active' : ''}`}
              onClick={() => setCurrentPage('datasets')}
            >
              Datasets
            </button>
            <button
              className={`nav-link ${currentPage === 'upload' ? 'active' : ''}`}
              onClick={() => setCurrentPage('upload')}
            >
              Upload
            </button>
            <button
              className={`nav-link ${currentPage === 'alerts' ? 'active' : ''}`}
              onClick={() => setCurrentPage('alerts')}
            >
              Alerts
            </button>
          </nav>
        </div>
      </header>
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  )
}

export default App
