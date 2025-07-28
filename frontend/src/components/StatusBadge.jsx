const LABELS = {
  stable: "已稳定可用",
  v1: "第一版可用",
  experimental: "实验性",
  planning: "规划中",
};

export function StatusBadge({ status, label }) {
  return <span className={`status-badge ${status || "planning"}`}>{label || LABELS[status] || "未说明"}</span>;
}
