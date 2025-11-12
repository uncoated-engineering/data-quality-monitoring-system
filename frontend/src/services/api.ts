import axios from 'axios';
import type { Dataset, QualityScore, Alert, DatasetProfile, QualityHistory, TrendAnalysis } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const datasetAPI = {
  uploadDataset: async (file: File, datasetName?: string): Promise<Dataset> => {
    const formData = new FormData();
    formData.append('file', file);
    if (datasetName) {
      formData.append('dataset_name', datasetName);
    }

    const response = await api.post('/api/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  listDatasets: async (): Promise<Dataset[]> => {
    const response = await api.get('/api/datasets');
    return response.data;
  },

  getDataset: async (datasetId: string): Promise<any> => {
    const response = await api.get(`/api/datasets/${datasetId}`);
    return response.data;
  },
};

export const qualityAPI = {
  assessQuality: async (datasetId: string): Promise<QualityScore> => {
    const response = await api.post(`/api/assess/${datasetId}`);
    return response.data;
  },

  getQualityHistory: async (datasetId: string, days: number = 30): Promise<QualityHistory[]> => {
    const response = await api.get(`/api/assess/${datasetId}/history`, {
      params: { days },
    });
    return response.data.history;
  },

  getQualityTrends: async (datasetId: string, days: number = 7): Promise<TrendAnalysis> => {
    const response = await api.get(`/api/assess/${datasetId}/trends`, {
      params: { days },
    });
    return response.data;
  },
};

export const profileAPI = {
  profileDataset: async (datasetId: string): Promise<DatasetProfile> => {
    const response = await api.get(`/api/profile/${datasetId}`);
    return response.data;
  },
};

export const alertAPI = {
  getAlerts: async (params?: {
    severity?: string;
    dataset_id?: string;
    active_only?: boolean;
  }): Promise<Alert[]> => {
    const response = await api.get('/api/alerts', { params });
    return response.data;
  },

  acknowledgeAlert: async (alertId: string): Promise<void> => {
    await api.post(`/api/alerts/${alertId}/acknowledge`);
  },

  getAlertSummary: async (): Promise<any> => {
    const response = await api.get('/api/alerts/summary');
    return response.data;
  },

  getAlertTrends: async (days: number = 7): Promise<any> => {
    const response = await api.get('/api/alerts/trends', {
      params: { days },
    });
    return response.data;
  },
};

export const deduplicationAPI = {
  findDuplicates: async (
    datasetId: string,
    params: {
      key_columns?: string[];
      fuzzy_columns?: string[];
      methods?: string[];
    }
  ): Promise<any> => {
    const response = await api.post(`/api/deduplication/${datasetId}`, {
      dataset_id: datasetId,
      ...params,
    });
    return response.data;
  },

  mergeDuplicates: async (datasetId: string, strategy: string = 'first'): Promise<any> => {
    const response = await api.post(`/api/deduplication/${datasetId}/merge`, null, {
      params: { strategy },
    });
    return response.data;
  },
};

export const reportAPI = {
  generateReport: async (datasetId: string): Promise<any> => {
    const response = await api.get(`/api/reports/${datasetId}`);
    return response.data;
  },
};
