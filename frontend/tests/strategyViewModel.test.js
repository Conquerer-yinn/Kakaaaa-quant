import test from "node:test";
import assert from "node:assert/strict";

import { buildStrategyMetrics, formatPercent } from "../src/pages/strategyViewModel.js";


test("formatPercent preserves zero and appends percent sign", () => {
  assert.equal(formatPercent(0), "0.00%");
  assert.equal(formatPercent(7), "7.00%");
  assert.equal(formatPercent(null), "-");
});


test("buildStrategyMetrics maps backend metadata to review cards", () => {
  const metrics = buildStrategyMetrics({
    candidate_event_count: 12,
    complete_sample_count: 9,
    skipped_incomplete_count: 2,
    skipped_missing_quote_count: 1,
    latest_event_date: "20260818",
    five_day_average_return: 3.25,
    five_day_positive_rate: 66.67,
  });

  assert.deepEqual(metrics, [
    { label: "候选事件", value: 12 },
    { label: "完整样本", value: 9 },
    { label: "未来窗口不足", value: 2 },
    { label: "行情缺失", value: 1 },
    { label: "最新事件日", value: "20260818" },
    { label: "5日平均收益", value: "3.25%" },
    { label: "5日正收益比例", value: "66.67%" },
  ]);
});


test("buildStrategyMetrics keeps empty state explicit", () => {
  const metrics = buildStrategyMetrics({});

  assert.equal(metrics[0].value, 0);
  assert.equal(metrics[4].value, "-");
  assert.equal(metrics[5].value, "-");
});
