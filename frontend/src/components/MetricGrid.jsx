export function MetricGrid({ items }) {
  return (
    <div className="metric-grid">
      {items.map((item) => (
        <article key={item.label} className="metric-item">
          <span className="metric-label">{item.label}</span>
          <strong className="metric-value">{item.value ?? "-"}</strong>
        </article>
      ))}
    </div>
  );
}
