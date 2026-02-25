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

Also redact live credentials from tracked archives, default `TUSHARE_HTTP_URL` to empty, and reject any explicitly configured non-HTTPS gateway.

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

### Task 3: Add workbook persistence and runner

**Files:**
- Create: `strategies/chinext_limit_up_workbook.py`
- Create: `strategies/run_chinext_limit_up_event_study.py`
- Create: `tests/strategies/test_chinext_limit_up_workbook.py`
- Create: `tests/strategies/test_run_chinext_limit_up_event_study.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing workbook tests**

Assert file names follow `创业板涨停事件研究_YYYYMMDD_YYYYMMDD.xlsx`, writing produces the three required sheets, and latest-file lookup selects the greatest end date.

- [ ] **Step 2: Verify workbook tests fail**

Run: `.venv/Scripts/python -m unittest tests.strategies.test_chinext_limit_up_workbook -v`

Expected: import failure because the workbook module is absent.

- [ ] **Step 3: Implement workbook functions**

The functions must satisfy this concrete contract:

```python
file_name = build_event_study_file_name("20260101", "20260331")
assert file_name == "创业板涨停事件研究_20260101_20260331.xlsx"
output_path = write_event_study_workbook(result, "20260101", "20260331", base_dir=temp_dir)
assert Path(output_path).exists()
latest = find_latest_event_study_workbook(base_dir=temp_dir)
assert latest.file_name == file_name
assert latest.start_date == "20260101"
assert latest.end_date == "20260331"
```

- [ ] **Step 4: Write failing runner tests**

Test `normalize_ymd`, default 120-calendar-day range, invalid reversed ranges, fetch-end buffering, and runner orchestration with an injected fake engine.

- [ ] **Step 5: Implement the runner**

The runner must satisfy this injectable contract:

```python
output_path = run_chinext_limit_up_event_study(
    start_date="20260101",
    end_date="20260331",
    base_dir=temp_dir,
    engine=fake_engine,
)
assert Path(output_path).exists()
assert fake_engine.calendar_requests == [("20260101", "20260414")]
```

The runner starts with `end_date + 14 calendar days` and doubles the window up to 56 days until the calendar contains at least five open sessions after the event end date. It then loads daily quotes for all returned dates, loads limit events only for the requested event interval, calculates the study, and writes the workbook.

- [ ] **Step 6: Verify GREEN**

Run: `.venv/Scripts/python -m unittest tests.strategies.test_chinext_limit_up_workbook tests.strategies.test_run_chinext_limit_up_event_study -v`

Expected: all persistence and runner tests pass.

### Task 4: Expose results through FastAPI with TDD

**Files:**
- Create: `backend/schemas/strategies.py`
- Create: `backend/services/strategy_data.py`
- Modify: `backend/api/routes.py`
- Create: `tests/backend/test_strategy_data.py`
- Create: `tests/backend/test_strategy_routes.py`

- [ ] **Step 1: Write failing service tests**

Write a temporary workbook and assert the response includes the latest file name, summary rows, run metadata, limited recent details, and a clear empty-state error.

- [ ] **Step 2: Verify RED**

Run: `.venv/Scripts/python -m unittest tests.backend.test_strategy_data -v`

Expected: import failure because the service module is absent.

- [ ] **Step 3: Implement response schemas and service**

```python
class StrategyStudyRunRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None

class StrategyStudyResponse(BaseModel):
    success: bool
    strategy_key: str
    title: str
    description: str
    file_name: str | None = None
    updated_at: str | None = None
    summary: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    detail_columns: list[str] = Field(default_factory=list)
    details: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
```

- [ ] **Step 4: Write failing route tests**

Assert OpenAPI contains GET and POST `/strategies/chinext-limit-up-event-study` paths and direct route calls return the declared response model.

- [ ] **Step 5: Add GET and POST routes**

GET reads the latest workbook. POST runs the synchronous research task and then reads the new workbook. Both preserve readable domain errors in the response.

- [ ] **Step 6: Verify GREEN**

Run: `.venv/Scripts/python -m unittest tests.backend.test_strategy_data tests.backend.test_strategy_routes -v`

Expected: backend strategy tests pass.

### Task 5: Replace the strategy placeholder page

**Files:**
- Modify: `frontend/src/api/client.js`
- Modify: `frontend/src/pages/StrategiesPage.jsx`
- Modify: `frontend/src/styles.css`
- Modify: `backend/services/frontend_data.py`

- [ ] **Step 1: Add the two API client methods**

```javascript
getChinextLimitUpStudy(limit = 100) {
  return request(`/strategies/chinext-limit-up-event-study?limit=${limit}`);
},
runChinextLimitUpStudy(payload = {}) {
  return request("/strategies/chinext-limit-up-event-study/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
},
```

- [ ] **Step 2: Implement the real page**

Use existing `SectionCard`, `MetricGrid`, `DataTable`, feedback, and button styles. Load current results on mount, run the default 120-day study on button click, and render only backend-provided data.

- [ ] **Step 3: Update dashboard wording**

Replace “策略占位” with the new event-study capability and link description.

- [ ] **Step 4: Verify the production build**

Run: `cd frontend && npm run build`

Expected: Vite build succeeds with no compile errors.

### Task 6: Register and document the strategy

**Files:**
- Modify: `strategies/strategy_registry.yaml`
- Modify: `strategies/README.md`
- Modify: `README.md`
- Modify: `project_memory/handoff/PROJECT_STATUS.md`
- Create: `project_memory/decisions/2026-02-20_创业板涨停事件研究第一版.md`

- [ ] **Step 1: Replace the fake registry entry**

Register `chinext_limit_up_event_study`, point at the runner, keep `enabled: false`, and state that it is a research job rather than an automated trading strategy.

- [ ] **Step 2: Document run and review flows**

Document CLI usage, API paths, Excel sheets, research caveats, and frontend location.

- [ ] **Step 3: Update project memory**

Record the event definition, return convention, intentional non-goals, and next iteration options.

### Task 7: Full verification and delivery

**Files:**
- Modify only files required by failures found during verification.

- [ ] **Step 1: Run all Python tests**

Run: `.venv/Scripts/python -m unittest discover -s tests -t . -p "test_*.py" -v`

Expected: all tests pass with zero failures.

- [ ] **Step 2: Run Python static parsing and import smoke checks**

Parse every tracked Python file with `ast.parse`, import `backend.main`, and verify both new OpenAPI paths exist.

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`

Expected: build succeeds.

- [ ] **Step 4: Run a real short-range study**

Run: `.venv/Scripts/python strategies/run_chinext_limit_up_event_study.py --start-date <bounded historical date> --end-date <bounded historical date>`

Expected: an ignored workbook is written under `storage/strategy_results/` and the GET service reads it. If credentials or network block this step, record the exact gap without weakening automated verification.

- [ ] **Step 5: Review diff and commit with Lore trailers**

Commit documentation, implementation, and verification evidence in small coherent commits. Push `codex/feature-development` after all verification passes.
