export function formatPercent(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? `${numeric.toFixed(2)}%` : "-";
}


export function buildStrategyMetrics(metadata = {}) {
  return [
    { label: "候选事件", value: metadata.candidate_event_count ?? 0 },
    { label: "完整样本", value: metadata.complete_sample_count ?? 0 },
    { label: "未来窗口不足", value: metadata.skipped_incomplete_count ?? 0 },
    { label: "行情缺失", value: metadata.skipped_missing_quote_count ?? 0 },
    { label: "排除ST", value: metadata.excluded_st_count ?? 0 },
    { label: "排除次新", value: metadata.excluded_recent_listing_count ?? 0 },
    { label: "基础信息缺失", value: metadata.missing_stock_basic_count ?? 0 },
    { label: "基准行情缺失", value: metadata.missing_benchmark_count ?? 0 },
    { label: "最新事件日", value: metadata.latest_event_date || "-" },
    { label: "5日平均收益", value: formatPercent(metadata.five_day_average_return) },
    { label: "5日正收益比例", value: formatPercent(metadata.five_day_positive_rate) },
  ];
}
