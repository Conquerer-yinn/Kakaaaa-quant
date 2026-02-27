# Chinext Event Study V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the Chinext limit-up event study with benchmark-adjusted returns, transparent research groups, sample filters, and quality reporting across Excel, API, and React.

**Architecture:** Extend the existing pure pandas calculation instead of creating a second engine. The runner supplies benchmark, stock metadata, and market-regime inputs in bulk; workbook, API, and frontend remain thin projections of the same result object.

**Tech Stack:** Python 3, pandas, openpyxl, FastAPI/Pydantic, React 18, Node built-in tests, Vite.

---

### Task 1: Benchmark-adjusted research math

**Files:**
- Modify: `strategies/chinext_limit_up_event_study.py`
- Modify: `tests/strategies/test_chinext_limit_up_event_study.py`

- [ ] **Step 1: Write failing benchmark tests**

```python
result = build_event_study(
    trade_dates=trade_dates,
    event_start_date="20260105",
    event_end_date="20260105",
    daily_by_date=daily_by_date,
    limit_by_date=limit_by_date,
    benchmark_close_by_date=benchmark_close_by_date,
)
row = result.details.iloc[0]
self.assertEqual(row["5日基准收益率(%)"], 5.0)
self.assertEqual(row["5日超额收益率(%)"], 5.0)
```

- [ ] **Step 2: Verify RED**

Run: `.venv/Scripts/python -m unittest tests.strategies.test_chinext_limit_up_event_study -v`

Expected: FAIL because `build_event_study` does not accept benchmark inputs or emit excess-return fields.

- [ ] **Step 3: Implement benchmark and excess-return columns**

Keep raw returns when benchmark values are missing, emit `None` for affected benchmark/excess values, and increment `missing_benchmark_count` once per complete stock sample.

- [ ] **Step 4: Add summary assertions**

Assert the 1/3/5-day summary includes benchmark mean, excess mean, and excess-positive rate.

- [ ] **Step 5: Verify GREEN**

Run the same unittest command and expect all event-study tests to pass.

### Task 2: Sample filters and research groups

**Files:**
- Modify: `strategies/chinext_limit_up_event_study.py`
- Modify: `tests/strategies/test_chinext_limit_up_event_study.py`

- [ ] **Step 1: Write failing filter tests**

Create events for a normal stock, an ST stock, a 30-day-old listing, and a stock missing from `stock_basic_df`. Assert only the normal and unknown-metadata events remain, while all quality counters are explicit.

- [ ] **Step 2: Write failing group tests**

```python
self.assertEqual(details.loc[details["股票代码"] == "300001.SZ", "连板阶段"].item(), "首板")
self.assertEqual(details.loc[details["股票代码"] == "301002.SZ", "连板阶段"].item(), "连板")
self.assertEqual(classify_market_regime(30), "弱")
self.assertEqual(classify_market_regime(31), "中")
self.assertEqual(classify_market_regime(61), "强")
```

- [ ] **Step 3: Verify RED**

Run the event-study unittest module and confirm failures are caused by missing filters/groups.

- [ ] **Step 4: Implement filters, labels, group summary, and quality summary**

Use 60 calendar days as the listing-age boundary and fixed 30/60 market thresholds from the V2 spec.

- [ ] **Step 5: Verify GREEN**

Run the event-study unittest module and expect all tests to pass.

### Task 3: Runner and five-sheet workbook

**Files:**
- Modify: `strategies/run_chinext_limit_up_event_study.py`
- Modify: `strategies/chinext_limit_up_workbook.py`
- Modify: `tests/strategies/test_run_chinext_limit_up_event_study.py`
- Modify: `tests/strategies/test_chinext_limit_up_workbook.py`

- [ ] **Step 1: Write failing runner tests**

Assert the fake engine receives exactly one `get_stock_basic()` call and one ranged `get_index_daily("399006.SZ", start_date, end_date)` call.

- [ ] **Step 2: Write failing workbook tests**

Assert the saved sheet order is `研究摘要`, `分组统计`, `样本质量`, `事件明细`, `运行信息`.

- [ ] **Step 3: Verify RED**

Run both runner and workbook unittest modules and confirm the V1 behavior lacks the new calls/sheets.

- [ ] **Step 4: Implement bulk input adaptation and workbook sheets**

Convert the index DataFrame into a date-to-close map, derive event-day market regimes from each limit table, and pass all inputs to the pure calculator.

- [ ] **Step 5: Verify GREEN**

Run the two unittest modules and expect all tests to pass.

### Task 4: API projection

**Files:**
- Modify: `backend/schemas/strategies.py`
- Modify: `backend/services/strategy_data.py`
- Modify: `tests/backend/test_strategy_data.py`

- [ ] **Step 1: Write failing API-service assertions**

Assert `StrategyStudyResponse` returns non-empty `group_summary` and `quality_summary` from a V2 workbook and exposes quality counters in metadata.

- [ ] **Step 2: Verify RED**

Run: `.venv/Scripts/python -m unittest tests.backend.test_strategy_data -v`

Expected: FAIL because the response model and service do not read the new sheets.

- [ ] **Step 3: Implement schema and service projection**

Read both sheets from the exact workbook chosen by GET/POST and normalize values with the existing JSON-safe conversion.

- [ ] **Step 4: Verify GREEN**

Run the backend strategy-data tests and expect all tests to pass.

### Task 5: V2 strategy page

**Files:**
- Modify: `frontend/src/pages/strategyViewModel.js`
- Modify: `frontend/src/pages/StrategiesPage.jsx`
- Modify: `frontend/tests/strategyViewModel.test.js`

- [ ] **Step 1: Write failing view-model assertions**

Assert metrics include ST exclusion, recent-listing exclusion, and missing benchmark counts.

- [ ] **Step 2: Verify RED**

Run: `cd frontend && node --test tests/strategyViewModel.test.js`

Expected: FAIL because V1 metrics omit quality counters.

- [ ] **Step 3: Implement V2 sections**

Render the existing summary plus separate “分组统计” and “样本质量” tables. Update the research boundary copy to name `399006.SZ` and excess returns.

- [ ] **Step 4: Verify GREEN and build**

Run `npm test` and `npm run build`; expect all tests and the Vite production build to pass.

### Task 6: Documentation and delivery

**Files:**
- Modify: `README.md`
- Modify: `strategies/README.md`
- Modify: `project_memory/handoff/PROJECT_STATUS.md`
- Create: `project_memory/decisions/2026-03-25_创业板涨停事件研究V2.md`

- [ ] **Step 1: Document all V2 thresholds and caveats**

Record benchmark code, listing-age filter, market-regime thresholds, missing-data behavior, and the unchanged non-trading-strategy boundary.

- [ ] **Step 2: Run full verification**

Run Python unittest discovery, frontend tests/build, AST parsing, pip check, `git diff --check`, HTTP smoke, and browser console inspection.

- [ ] **Step 3: Request focused code review**

Review the full V2 diff for research bias, missing-data handling, API consistency, and test adequacy. Resolve every Critical/Important issue.

- [ ] **Step 4: Commit and push**

Use Lore trailers, push `codex/feature-development`, and verify the remote ref equals local HEAD.
