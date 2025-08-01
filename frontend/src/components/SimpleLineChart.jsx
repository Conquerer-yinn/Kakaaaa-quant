function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return Number(value);
}

export function SimpleLineChart({ title, rows, xKey, yKey, suffix = "" }) {
  const points = rows
    .map((row) => ({ x: row[xKey], y: formatNumber(row[yKey]) }))
    .filter((point) => point.y !== null);

  if (!points.length) {
    return (
      <div className="chart-card empty">
        <p className="chart-title">{title}</p>
        <p>当前没有可绘制的数据。</p>
      </div>
    );
  }

  const min = Math.min(...points.map((point) => point.y));
  const max = Math.max(...points.map((point) => point.y));
  const range = max - min || 1;
  const width = 480;
  const height = 180;

  const line = points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width;
      const y = height - ((point.y - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");

  const latest = points[points.length - 1];

  return (
    <div className="chart-card">
      <div className="chart-meta">
        <p className="chart-title">{title}</p>
        <strong>
          最新值 {latest.y}
          {suffix}
        </strong>
      </div>
      <svg viewBox={`0 0 ${width} ${height + 24}`} className="chart-svg" preserveAspectRatio="none">
        <defs>
          <linearGradient id={`fill-${yKey}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="rgba(13, 148, 136, 0.35)" />
            <stop offset="100%" stopColor="rgba(13, 148, 136, 0.02)" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke="#0f766e" strokeWidth="3" points={line} />
        <polyline
          fill={`url(#fill-${yKey})`}
          stroke="none"
          points={`0,${height} ${line} ${width},${height}`}
        />
      </svg>
      <div className="chart-footnote">
        <span>{points[0].x}</span>
        <span>{latest.x}</span>
      </div>
    </div>
  );
}
