# 策略研究目录

这个目录存放策略研究代码、贴近代码的研究说明，以及可纳入日常运行的策略注册信息。

## 已落地研究

### 创业板涨停后 5 日事件研究

入口：`strategies/run_chinext_limit_up_event_study.py`

研究口径：

1. 识别代码以 `300`、`301` 开头且 `limit_list_d.limit == U` 的涨停事件。
2. 只保留事件日有有效收盘价、且之后存在完整 5 个交易日行情的样本。
3. 排除名称包含 ST 的样本，以及事件日上市未满 60 个自然日的样本。
4. 计算事件后第 1、3、5 个交易日的收盘收益率。
5. 使用创业板指数 `399006.SZ` 计算同期基准收益和超额收益。
6. 按首板/连板，以及事件日全市场涨停数划分的弱/中/强环境分组。
7. 计算 5 日窗口内最高和最低收盘收益率。
8. 显式输出所有排除项与缺失项，不静默丢弃样本。

市场环境阈值：

- `弱`：涨停数不超过 30 家
- `中`：涨停数 31–60 家
- `强`：涨停数超过 60 家

运行最近 120 个自然日：

```powershell
.venv\Scripts\python.exe strategies\run_chinext_limit_up_event_study.py
```

运行指定区间：

```powershell
.venv\Scripts\python.exe strategies\run_chinext_limit_up_event_study.py `
  --start-date 20260101 `
  --end-date 20260331
```

输出目录：`storage/strategy_results/`。

工作簿包含：

- `研究摘要`
- `分组统计`
- `样本质量`
- `事件明细`
- `运行信息`

也可以在 `/strategies` 页面运行和查看，或通过以下 API 调用：

- `GET /strategies/chinext-limit-up-event-study`
- `POST /strategies/chinext-limit-up-event-study/run`

## 研究边界

当前结果属于事件研究，不包含交易成本、滑点、仓位、买卖执行或盘中成交模拟。超额收益只表示相对 `399006.SZ` 的历史差异，不能直接解释为已验证盈利的交易策略。

是否纳入后续日常运行，由 `strategies/strategy_registry.yaml` 控制。V2 仍默认 `enabled: false`，避免研究任务被误当成正式交易任务。

## 研究记录规范

每个策略至少维护两个文件：

1. `策略名.py`：策略代码本体。
2. `策略名.md`：研究笔记，记录口径、样本区间、阶段性结论和已知问题。

研究笔记建议按时间倒序追加，不删除历史结论，方便回看判断当时的依据。

## 策略脚本约定

1. 策略核心逻辑写成纯函数：输入 DataFrame，输出 DataFrame，方便离线测试。
2. 需要取数时统一走 `data_engine/`，不在策略里直接调用第三方接口。
3. 简单筛选类策略结果统一走 `strategies/strategy_output.py`；事件研究类输出到 `storage/strategy_results/`。
4. 需要被 `run_strategies.py` 调度的策略，暴露 `run(trade_date)` 入口。

## 研究 -> 日常运行的完整流程

1. **研究**：写 `策略名.py`，核心筛选逻辑保持纯函数，用测试或小样本验证口径。
2. **登记**：在 `strategy_registry.yaml` 中登记，`enabled: false` 起步。
3. **试运行**：手动运行脚本或 `python strategies/run_strategies.py --trade-date YYYYMMDD` 观察输出。
4. **启用**：确认稳定后把 `enabled` 改为 `true`，视需要开 `push`。
5. **复盘**：结果落表后做人工复盘，结论写回 `策略名.md`。

## 复盘笔记模板

```markdown
## YYYY-MM-DD 复盘

- 样本区间：
- 样本数量：
- 关键统计：
- 结论：
- 待验证问题：
```
