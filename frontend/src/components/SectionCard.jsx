export function SectionCard({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`section-card ${className}`.trim()}>
      <div className="section-head">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {action ? <div className="section-action">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}
