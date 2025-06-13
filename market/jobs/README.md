# 行情任务目录

这个目录存放可以直接运行的行情分析任务。

当前目录中的任务分成两类：

1. 独立标准任务
   例如 `run_daily_basics.py`
2. 综合研究任务
   例如 `run_market_sentiment.py`

每个任务脚本尽量只负责：

1. 接收参数或日期范围
2. 调用 `data_engine/` 获取原始数据
3. 视需要调用 `market/indicators/` 中的可复用指标逻辑
4. 调用 `storage/` 输出结果

任务入口文件不要承载太多核心业务逻辑。
如果某个任务只是一次性的小脚本，也可以先直接写在这里，后续再抽离复用部分。

当前约定：

1. 不为了目录整齐，强行拆散已经有真实使用价值的综合任务。
2. 一个任务写入同一个 Excel 的多个 sheet 是允许的。
3. 只有当某个模块本身具备单独运行、单独输出、单独复用价值时，再考虑升级成独立任务。

## `run_daily_basics.py` 运行逻辑

`run_daily_basics.py` 目前支持两种模式：

1. 初始化 / 手动区间模式
2. 增量更新模式

它当前仍然保留，主要价值是：

- 作为第一条标准任务模板
- 作为 FastAPI 任务封装示例
- 作为后续新增标准任务时可复用的参考

需要注意的是：

- 当前前端历史页已经不再单独展示 `daily-basics`
- 当前项目的历史展示重心已经转到 `market-sentiment`

## `run_market_sentiment.py` 运行逻辑

`run_market_sentiment.py` 当前已经切换成更贴合真实复盘工作流的模式：

1. 默认维护历史主表，而不是“近期工作簿”。
2. 历史主表命名规则为：`历史数据_起始日期_结束日期.xlsx`。
3. 每次补数时先生成：`补充数据_起始日期_结束日期.xlsx`，并写入 `storage/backups/`。
4. 再把补充数据并回历史主表，保留 `总览` sheet 和用户手工维护的图表模板。
5. 测试运行统一输出：`测试数据_起始日期_结束日期.xlsx`。

它会更新四个 sheet：

1. `总览`
2. `总市场数据`
3. `高度观察`
4. `创业板专区`

### 默认增量逻辑

1. 程序优先识别 `storage/data_master/` 下最新的历史主表。
2. 如果不传 `--start-date`，则默认从主表最后一天的下一天开始补数。
3. 如果传了 `--start-date`，则按指定起点补数，但仍然写回历史主表。
4. 前端历史页只读取最新历史主表里的最近 20 个交易日。
5. 后端读取时会过滤掉当前前端不需要的“位置 / 相对中枢”等列。

### `TUSHARE_REQUEST_DELAY`

这个脚本没有单独提供 `--request-delay` 参数，而是读取环境变量 `TUSHARE_REQUEST_DELAY`。
目前建议值是 `0.5`，如果还是频繁限流，可以提高到 `1` 或更高。

### 推荐用法

基于当前历史主表补到今天：

```powershell
$env:TUSHARE_REQUEST_DELAY='0.5'
python market/jobs/run_market_sentiment.py
```

补到指定日期：

```powershell
$env:TUSHARE_REQUEST_DELAY='0.5'
python market/jobs/run_market_sentiment.py --end-date 20260402
```

生成测试工作簿：

```powershell
$env:TUSHARE_REQUEST_DELAY='0.5'
python market/jobs/run_market_sentiment.py --test-mode --start-date 20260321 --end-date 20260402
```

### 注意事项

1. 该任务会自动回补缓冲区，用于重算近十日高度和次日反馈。
2. 程序更新数据 sheet 时，会尽量保留工作簿里的图表页和其他模板页。
3. 每个数据 sheet 会被包装成 Excel Table，便于图表模板自动扩展到新增数据行。
4. `总览` 只会重写上方摘要区域，不应该把图表放在前 24 行。
5. 如果目标 Excel 正在打开，程序会给出明确报错提示。
6. 当前仍有一个遗留问题：历史主表更新后，Excel 可能修复 `externalLinks` 记录，且图表未必自动刷新，详见 `project_memory/decisions/2026-04-02_历史主表更新后Excel外部链接与图表遗留问题.md`。

## 当前最小 API 封装

当前项目已补充最小 FastAPI 封装，可直接调用这两个任务：

- `POST /tasks/daily-basics/run`
- `POST /tasks/market-sentiment/run`
- `GET /tasks/market-sentiment/{task_id}`
- `POST /tasks/market-sentiment/{task_id}/cancel`

其中 `market-sentiment` 已支持后台执行、轮询与取消。

## 三类卡片任务

### `push_post_close_card.py`

用于根据原始数据层和指标计算层，直接构造盘后飞书卡片，并推送到飞书机器人。

### `push_auction_card.py`

用于根据原始竞价数据直接构造飞书卡片，并推送到飞书机器人。

### `push_intraday_card.py`

用于根据实时原始数据构造盘中节奏卡片，并推送到飞书机器人。

当前统一共识：

1. 三类卡片都不再依赖 Excel 视图层取数。
2. 三类卡片都已经接入后端刷新 / 发送接口。
3. 三类卡片都已经完成真实 webhook 发送联调。
4. 盘中卡片允许因为实时权限不足而降级。

### 推荐用法

先本地检查卡片内容：

```powershell
$env:TUSHARE_REQUEST_DELAY='0.5'
python market/jobs/push_post_close_card.py --trade-date 20260401 --dry-run
python market/jobs/push_auction_card.py --trade-date 20260331 --dry-run
python market/jobs/push_intraday_card.py --trade-date 20260401 --dry-run
```

实际推送：

```powershell
$env:TUSHARE_REQUEST_DELAY='0.5'
$env:FEISHU_BOT_WEBHOOK='你的飞书机器人 webhook'
python market/jobs/push_post_close_card.py --trade-date 20260401
python market/jobs/push_auction_card.py --trade-date 20260331
python market/jobs/push_intraday_card.py --trade-date 20260401
```
