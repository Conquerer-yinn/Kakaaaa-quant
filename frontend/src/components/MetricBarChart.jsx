import { useMemo, useState } from "react";

function toNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return Number(value);
}

export function MetricBarChart({ title, rows, xKey, yKey }) {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const points = useMemo(
    () =>
      rows
        .map((row) => ({ x: row[xKey], y: toNumber(row[yKey]) }))
        .filter((point) => point.y !== null),
    [rows, xKey, yKey],
  );

  if (!points.length) {
    return (
      <div className="chart-card empty">
        <p className="chart-title">{title}</p>
        <p>当前没有可绘制的数据。</p>
      </div>
    );
  }

  const width = 620;
  const height = 220;
  const max = Math.max(...points.map((point) => point.y), 1);
  const barWidth = width / Math.max(points.length * 1.35, 1);
  const gap = barWidth * 0.35;
  const latest = points[points.length - 1];
  const hoveredPoint = hoveredIndex === null ? null : points[hoveredIndex];

  return (
    <div className="chart-card">
      <div className="chart-meta">
        <p className="chart-title">{title}</p>
        <strong>最新值 {latest.y}</strong>
      </div>
      <div className="chart-stage">
        {hoveredPoint ? (
          <div className="chart-tooltip" role="status" aria-live="polite">
            <strong>{hoveredPoint.x}</strong>
            <span>{yKey}</span>
            <b>{hoveredPoint.y}</b>
          </div>
        ) : null}
        <svg
          viewBox={`0 0 ${width} ${height + 30}`}
          className="chart-svg"
          preserveAspectRatio="none"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          {points.map((point, index) => {
            const baseBarHeight = (point.y / max) * (height - 16);
            const baseX = index * (barWidth + gap) + 8;
            const baseY = height - baseBarHeight;
            const isLatest = index === points.length - 1;
            const isHovered = index === hoveredIndex;
            const growWidth = isHovered ? Math.min(barWidth * 0.18, 6) : 0;
            const growHeight = isHovered ? Math.min(baseBarHeight * 0.08 + 4, 16) : 0;
            const rectWidth = barWidth + growWidth;
            const rectHeight = baseBarHeight + growHeight;
            const rectX = baseX - growWidth / 2;
            const rectY = Math.max(0, baseY - growHeight);
            return (
              <g
                key={`${point.x}-${index}`}
                className={`chart-bar-group${isHovered ? " hovered" : ""}`}
                onMouseEnter={() => setHoveredIndex(index)}
              >
                <rect
                  x={rectX}
                  y={rectY}
                  width={rectWidth}
                  height={rectHeight}
                  rx="6"
                  fill={isLatest ? "#b45309" : "#0f766e"}
                  opacity={isHovered ? "1" : isLatest ? "0.96" : "0.86"}
                />
                {isHovered ? (
                  <text x={rectX + rectWidth / 2} y={Math.max(16, rectY - 8)} textAnchor="middle" className="chart-hover-value">
                    {point.y}
                  </text>
                ) : null}
              </g>
            );
          })}
        </svg>
      </div>
      <div className="chart-footnote">
        <span>{hoveredPoint ? hoveredPoint.x : points[0].x}</span>
        <span>{hoveredPoint ? `${yKey} ${hoveredPoint.y}` : latest.x}</span>
      </div>
    </div>
  );
}
