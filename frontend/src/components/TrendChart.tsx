import type { QualityHistory } from '../types';

interface TrendChartProps {
  data: QualityHistory[];
}

function TrendChart({ data }: TrendChartProps) {
  if (data.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
      No trend data available
    </div>;
  }

  // Simple SVG chart
  const width = 800;
  const height = 300;
  const padding = 40;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;

  const maxScore = 100;
  const minScore = 0;

  const points = data.map((item, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth;
    const y = padding + chartHeight - ((item.overall_score - minScore) / (maxScore - minScore)) * chartHeight;
    return { x, y, ...item };
  });

  const pathData = points.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  ).join(' ');

  return (
    <div style={{ overflowX: 'auto' }}>
      <svg width={width} height={height} style={{ minWidth: '600px' }}>
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(score => {
          const y = padding + chartHeight - ((score - minScore) / (maxScore - minScore)) * chartHeight;
          return (
            <g key={score}>
              <line
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
              />
              <text
                x={padding - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="12"
                fill="#6b7280"
              >
                {score}
              </text>
            </g>
          );
        })}

        {/* Trend line */}
        <path
          d={pathData}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="3"
        />

        {/* Data points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="4"
            fill="#3b82f6"
          >
            <title>
              {new Date(p.timestamp).toLocaleDateString()}: {p.overall_score.toFixed(1)}
            </title>
          </circle>
        ))}

        {/* X-axis labels */}
        {points.filter((_, i) => i % Math.ceil(points.length / 5) === 0).map((p, i) => (
          <text
            key={i}
            x={p.x}
            y={height - padding + 20}
            textAnchor="middle"
            fontSize="12"
            fill="#6b7280"
          >
            {new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </text>
        ))}

        {/* Y-axis label */}
        <text
          x={padding - 30}
          y={padding - 10}
          fontSize="12"
          fill="#6b7280"
          fontWeight="600"
        >
          Score
        </text>
      </svg>
    </div>
  );
}

export default TrendChart;
