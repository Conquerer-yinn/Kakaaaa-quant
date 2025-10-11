# 策略目录

这个目录用于存放策略代码，以及与策略直接相关的研究记录。

建议做法：

1. 策略代码放在这里
2. 策略阶段性结论、问题记录、灵感笔记，也直接放在这里
3. 是否纳入日常运行，由 `strategies/strategy_registry.yaml` 控制

这样记录会更贴近代码，后续回看也更方便。

## 研究记录规范

每个策略至少维护两个文件：

1. `策略名.py`：策略代码本体。
2. `策略名.md`：研究笔记，记录口径、样本区间、阶段性结论和已知问题。

研究笔记建议按时间倒序追加，不删除历史结论，方便回看判断当时的依据。

## 策略脚本约定

1. 策略核心逻辑写成纯函数：输入 DataFrame，输出 DataFrame，方便离线测试。
2. 需要取数时统一走 `data_engine/`，不在策略里直接调用第三方接口。
3. 结果输出统一走 `strategies/strategy_output.py`，不自行管理文件路径。
4. 需要被 `run_strategies.py` 调度的策略，暴露 `run(trade_date)` 入口。

## 研究 -> 日常运行的完整流程

1. **研究**：写 `策略名.py`，核心筛选逻辑保持纯函数，用测试或小样本验证口径。
2. **登记**：在 `strategy_registry.yaml` 中登记，`enabled: false` 起步。
3. **试运行**：手动 `python strategies/策略名.py` 或 `python strategies/run_strategies.py --trade-date YYYYMMDD` 观察输出。
4. **启用**：确认稳定后把 `enabled` 改为 `true`，视需要开 `push`。
5. **复盘**：结果统一落在 `storage/data_master/策略数据_策略名.xlsx`，人工复盘结论写回 `策略名.md`。

## 复盘笔记模板

```markdown
## YYYY-MM-DD 复盘

- 样本区间：
- 样本数量：
- 关键统计：
- 结论：
- 待验证问题：
```
