interface DimensionScoresProps {
  scores: { [key: string]: number };
}

function DimensionScores({ scores }: DimensionScoresProps) {
  const getProgressClass = (score: number) => {
    if (score >= 90) return 'progress-excellent';
    if (score >= 70) return 'progress-good';
    if (score >= 50) return 'progress-fair';
    return 'progress-poor';
  };

  return (
    <div className="dimension-scores">
      {Object.entries(scores).map(([dimension, score]) => (
        <div key={dimension} className="dimension-item">
          <div className="dimension-label">{dimension}</div>
          <div className="progress-bar">
            <div
              className={`progress-fill ${getProgressClass(score)}`}
              style={{ width: `${score}%` }}
            />
          </div>
          <div className="dimension-value">{score.toFixed(1)}%</div>
        </div>
      ))}
    </div>
  );
}

export default DimensionScores;
