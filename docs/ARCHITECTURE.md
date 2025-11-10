# 架构总览

Kaka_Quant 是围绕真实 A 股研究工作流搭建的轻量工作台，整体分三层。

## 三层结构

```text
原始数据层   data_engine/          Tushare 封装：日历、行情、涨跌停、竞价、实时
指标计算层   market/indicators/    每日基础、总市场、高度、创业板、反馈、位置
输出视图层   storage/ (Excel)      市场情绪主表、每日基础主表、策略复盘表
             market/push_views/    盘后 / 竞价 / 盘中三类飞书卡片
             frontend/             React 展示壳
```

约定：

1. 输出视图层不反向取数：飞书卡片和前端都直接基于原始数据层与指标计算层生成，不从 Excel 反读。
2. 业务逻辑不绕过 `storage/` 写 Excel。
3. 策略层（`strategies/`）复用同一套数据与存储设施，注册表决定日常运行范围。

## 请求与数据流

```text
前端 (React)
   │  HTTP
   ▼
backend/ (FastAPI)
   ├── task_registry / task_runner     同步任务：daily-basics
   ├── task_manager                    后台任务：market-sentiment（线程池 + 取消）
   ├── frontend_data                   历史主表读取（最近 N 个交易日）
   ├── push_cards                      三类卡片：快照 -> 卡片 JSON -> 飞书
   └── strategy_data                   策略注册表暴露
   │
   ▼
market/jobs/                            可独立运行的任务入口
   │
   ▼
market/indicators/ + data_engine/       指标计算与取数
   │
   ▼
storage/ExcelHelper                     主表 / 备份 / 表格区域维护
```

## 任务模型

1. **独立标准任务**（daily-basics）：请求进来同步执行，直接返回结果。
2. **综合研究任务**（market-sentiment）：进后台线程池，返回 `task_id`，
   前端轮询状态，支持协作式取消（`should_cancel` 回调在安全点检查）。

## 历史主表机制

- 主表命名 `历史数据_起始_结束.xlsx`，每次增量补数：
  1. 生成 `补充数据_区间.xlsx` 到备份目录；
  2. 与当前主表合并去重；
  3. 主表滚动改名覆盖新区间，旧表进备份。
- 测试运行走 `测试数据_区间.xlsx`，不污染主表。
