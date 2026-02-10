import test from "node:test";
import assert from "node:assert/strict";

import { buildStrategyMetrics, formatPercent } from "../src/pages/strategyViewModel.js";


test("formatPercent preserves zero and appends percent sign", () => {
  assert.equal(formatPercent(0), "0.00%");
  assert.equal(formatPercent(7), "7.00%");
  assert.equal(formatPercent(null), "-");
});

