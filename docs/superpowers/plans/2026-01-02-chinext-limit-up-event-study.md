# Chinext Limit-Up Event Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real strategy-research vertical slice: a reproducible Chinext limit-up event study with Excel output, API access, a React review page, security cleanup, and automated tests.

**Architecture:** Keep research math pure in `strategies/chinext_limit_up_event_study.py`, isolate workbook naming and persistence in `strategies/chinext_limit_up_workbook.py`, and let a thin runner coordinate Tushare data collection. The backend only adapts the runner/workbook into existing FastAPI patterns; the frontend consumes one stable response shape and never fabricates results.

**Tech Stack:** Python 3, pandas, openpyxl, FastAPI/Pydantic, React 18, Vite, `unittest`.

---

### Task 1: Lock the security baseline

**Files:**
- Create: `tests/test_config_security.py`
- Modify: `common/config.py`
- Create: `.env.example`

- [ ] **Step 1: Write the failing security test**

```python
class ConfigSecurityTest(unittest.TestCase):
    def test_sensitive_environment_values_have_no_nonempty_default(self):
        assignments = load_assignments("common/config.py")
        for name in ("TUSHARE_TOKEN", "FEISHU_BOT_WEBHOOK"):
            call = assignments[name]
            self.assertLessEqual(len(call.args), 1)

    def test_env_example_documents_required_credentials(self):
        content = Path(".env.example").read_text(encoding="utf-8")
        self.assertIn("TUSHARE_TOKEN=", content)
        self.assertIn("FEISHU_BOT_WEBHOOK=", content)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `.venv/Scripts/python -m unittest tests.test_config_security -v`

Expected: FAIL because sensitive calls contain non-empty defaults and `.env.example` is absent.

- [ ] **Step 3: Apply the existing local security change**

Apply commit `8e93a80` or make the equivalent minimal edit so both credentials only use environment variables and `.env.example` contains empty documented keys.

- [ ] **Step 4: Run the test and verify GREEN**

Run: `.venv/Scripts/python -m unittest tests.test_config_security -v`

Expected: 2 tests pass.

### Task 2: Implement the pure event-study calculation with TDD

**Files:**
- Create: `strategies/__init__.py`
- Create: `strategies/chinext_limit_up_event_study.py`
- Create: `tests/strategies/test_chinext_limit_up_event_study.py`

- [ ] **Step 1: Write failing tests for complete samples**

Create deterministic DataFrames for one `300001.SZ` limit-up event and six trading days. Assert the event row includes 1/3/5-day returns and 5-day high/low returns.

```python
result = build_event_study(
    trade_dates=TRADE_DATES,
    event_start_date="20260105",
    event_end_date="20260105",
    daily_by_date=daily_by_date,
    limit_by_date=limit_by_date,
)
self.assertEqual(result.complete_sample_count, 1)
self.assertEqual(result.details.iloc[0]["5日收益率(%)"], 10.0)
```

- [ ] **Step 2: Verify RED**

Run: `.venv/Scripts/python -m unittest tests.strategies.test_chinext_limit_up_event_study -v`

Expected: import failure because the module is absent.

- [ ] **Step 3: Implement the minimal pure API**

The public contract must support this complete usage without network or filesystem access:

```python
result = build_event_study(
    trade_dates=["20260105", "20260106", "20260107", "20260108", "20260109", "20260112"],
    event_start_date="20260105",
    event_end_date="20260105",
    daily_by_date=daily_by_date,
    limit_by_date=limit_by_date,
)
assert result.candidate_event_count == 1
assert result.complete_sample_count == 1
assert result.skipped_incomplete_count == 0
assert result.skipped_missing_quote_count == 0
assert result.details.loc[0, "5日收益率(%)"] == 10.0
assert result.summary.loc[result.summary["观察周期"] == "5日", "样本数"].item() == 1
```

Implement only code filtering, full-horizon validation, return calculation, stable empty columns, and summary aggregation needed by this contract.

- [ ] **Step 4: Add edge-case tests**

Cover non-Chinext codes, non-`U` rows, missing event close, incomplete five-day windows, empty samples, and summary positive-rate calculations.

- [ ] **Step 5: Verify GREEN**

Run: `.venv/Scripts/python -m unittest tests.strategies.test_chinext_limit_up_event_study -v`

Expected: all event-study tests pass.

