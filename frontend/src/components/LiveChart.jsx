import React from 'react';

/**
 * Reusable SVG mini line chart for live sensor data.
 * Props: data (array of numbers), color, label, unit, width, height, showArea
 */
export default function LiveChart({ data = [], color = '#3b82f6', label = '', unit = '', width = 220, height = 60, showArea = true }) {
  if (!data || data.length < 2) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 11 }}>
        Waiting for data...
      </div>
    );
  }

  const values = data.slice(-40);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const padding = 2;

  const points = values.map((v, i) => {
    const x = padding + (i / (values.length - 1)) * (width - padding * 2);
    const y = padding + (1 - (v - min) / range) * (height - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const areaPoints = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;
  const currentValue = values[values.length - 1];

  return (
    <div>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>{label}</span>
          <span style={{ fontSize: 13, color, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
            {currentValue?.toFixed(1)}{unit && <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 2 }}>{unit}</span>}
          </span>
        </div>
      )}
      <svg width={width} height={height} style={{ overflow: 'visible', display: 'block' }}>
        {showArea && (
          <polyline
            points={areaPoints}
            fill={`${color}15`}
            stroke="none"
          />
        )}
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Current value dot */}
        <circle
          cx={width - padding}
          cy={padding + (1 - (currentValue - min) / range) * (height - padding * 2)}
          r="3"
          fill={color}
        >
          <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
        </circle>
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>
        <span>{min.toFixed(1)}</span>
        <span>{max.toFixed(1)}</span>
      </div>
    </div>
  );
}
