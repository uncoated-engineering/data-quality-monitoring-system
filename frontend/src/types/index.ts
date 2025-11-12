export interface Dataset {
  dataset_id: string;
  dataset_name: string;
  uploaded_at: string;
  rows: number;
  columns: number;
}

export interface QualityScore {
  dataset_id: string;
  dataset_name: string;
  timestamp: string;
  overall_score: number;
  dimension_scores: {
    [key: string]: number;
  };
  total_records: number;
  metrics: QualityMetric[];
  passed_rules: number;
  failed_rules: number;
  warnings: number;
}

export interface QualityMetric {
  metric_id: string;
  dimension: string;
  name: string;
  value: number;
  max_value: number;
  unit: string;
  timestamp: string;
  details: any;
}

export interface Alert {
  alert_id: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'critical';
  rule_id: string;
  rule_name: string;
  dimension: string;
  message: string;
  dataset_id: string;
  metric_value: number;
  threshold: number;
  details: any;
  acknowledged: boolean;
}

export interface DatasetProfile {
  dataset_id: string;
  dataset_name: string;
  total_records: number;
  total_columns: number;
  timestamp: string;
  column_profiles: {
    [key: string]: ColumnProfile;
  };
  duplicate_count: number;
  duplicate_percentage: number;
}

export interface ColumnProfile {
  dtype: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  top_values?: { [key: string]: number };
}

export interface QualityHistory {
  timestamp: string;
  overall_score: number;
  dimension_scores: { [key: string]: number };
}

export interface TrendAnalysis {
  trend: 'improving' | 'degrading' | 'stable' | 'insufficient_data';
  change: number;
  current_score: number;
  previous_score: number;
  dimension_trends?: {
    [key: string]: {
      change: number;
      current: number;
      trend: string;
    };
  };
}
