import test from "node:test";
import assert from "node:assert/strict";

import { ROUTER_FUTURE } from "../src/routerFuture.js";


test("router opts into supported v7 transition behavior", () => {
  assert.deepEqual(ROUTER_FUTURE, {
    v7_startTransition: true,
    v7_relativeSplatPath: true,
  });
});
