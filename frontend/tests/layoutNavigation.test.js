import test from "node:test";
import assert from "node:assert/strict";

import { NAV_ITEMS } from "../src/components/layoutNavigation.js";


test("strategy navigation names the real research page", () => {
  const strategyItem = NAV_ITEMS.find((item) => item.to === "/strategies");

  assert.equal(strategyItem?.label, "策略研究");
});
