import type { TrendAnalysis } from '../types';

interface QualityScoreCardProps {
  score: number;
  label: string;
  trend?: TrendAnalysis | null;
}

function QualityScoreCard({ score, label, trend }: QualityScoreCardProps) {
  const getScoreClass = (score: number) => {
    if (score >= 90) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-fair';
    return 'score-poor';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="stat-card">
      <div className="score-display">
        <div className={`score-circle ${getScoreClass(score)}`}>
          {score.toFixed(1)}
        </div>
        <div className="stat-label">{label}</div>
        <div style={{ fontWeight: 600, marginTop: '0.5rem' }}>
          {getScoreLabel(score)}
        </div>
        {trend && trend.trend !== 'insufficient_data' && (
          <div className={`stat-change ${trend.change >= 0 ? 'positive' : 'negative'}`}>
            {trend.change >= 0 ? '↑' : '↓'} {Math.abs(trend.change).toFixed(1)}% vs last week
          </div>
        )}
      </div>
    </div>
  );
}

export default QualityScoreCard;
