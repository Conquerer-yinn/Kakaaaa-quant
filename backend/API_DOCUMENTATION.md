# Kaka_Quant API Documentation

这份文档是当前项目的人工维护接口文档。

它的定位是：

1. 给前后端联调提供稳定入口。
2. 给后端后续加接口时提供统一登记位置。
3. 补足 `/docs` 这类运行时 Swagger 页面不方便沉淀项目约定的问题。

## 文档入口

启动 FastAPI 后，可同时使用两类接口文档：

- 人工维护文档：`backend/API_DOCUMENTATION.md`
- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

## 基本约定

- Base URL：`http://127.0.0.1:8000`
- 请求与响应格式：`application/json`
- 日期字段默认使用 `YYYYMMDD`
- 当前接口以轻量封装为主，不引入数据库、分页体系、统一鉴权体系

## 1. 系统与任务接口

### `GET /health`

用途：服务健康检查。

响应示例：

```json
{
  "status": "ok",
  "service": "Kaka_Quant API",
  "available_task_count": 2
}
```

### `GET /tasks`

用途：返回当前后端已暴露任务列表。

响应核心字段：

- `tasks[].task_name`：任务唯一名
- `tasks[].task_type`：任务类型
- `tasks[].description`：任务说明
- `tasks[].accepted_params`：支持的参数
- `tasks[].output_target`：默认输出目标

### `POST /tasks/daily-basics/run`

用途：执行每日基础数据任务。

请求体：

```json
{
  "start_date": "20260101",
  "end_date": "20260413",
  "output_file": "daily_basics_test.xlsx"
}
```

字段说明：

- `start_date`：可选，首次初始化或手动补数时使用
- `end_date`：可选，默认到当天
- `output_file`：可选，自定义输出文件名

响应核心字段：

- `success`：是否执行成功
- `output_path`：输出文件路径
- `error_message`：失败时返回错误原因

### `POST /tasks/market-sentiment/run`

用途：以后台任务方式运行市场情绪更新任务。

请求体：

```json
{
  "start_date": "20260320",
  "end_date": "20260413",
  "output_file": null,
  "history": true
}
```

字段说明：

- `start_date`：可选，手动指定补数起点
- `end_date`：可选，默认到当天
- `output_file`：可选，手动指定输出文件名
- `history`：默认 `true`；`false` 时只生成测试工作簿

响应核心字段：

- `task_id`：后台任务唯一 ID
- `status`：初始状态
- `created`：是否创建成功

### `GET /tasks/market-sentiment/{task_id}`

用途：轮询后台任务状态。

路径参数：

- `task_id`：后台任务 ID

响应核心字段：

- `status`：`pending` / `running` / `cancelling` / `cancelled` / `succeeded` / `failed`
- `progress_message`：当前进度信息
- `cancel_requested`：是否已请求取消
- `result`：任务完成后的结果
- `error_message`：失败原因

### `POST /tasks/market-sentiment/{task_id}/cancel`

用途：请求取消后台任务。

路径参数：

- `task_id`：后台任务 ID

响应核心字段与任务状态查询一致。

## 2. 前端消费接口

### `GET /dashboard/summary`

用途：返回首页概览信息。

响应核心字段：

- `project_name`：项目名称
- `project_positioning`：项目定位
- `main_lines`：主线说明
- `capability_summary`：当前能力摘要
- `quick_links`：前端快捷入口

### `GET /market/history/market-sentiment`

用途：返回市场情绪历史数据，供前端历史页面展示。

查询参数：

- `limit`：可选，默认 `20`，范围 `10-120`

响应核心字段：

- `dataset`：数据集名称
- `file_name`：当前读取的历史主表文件名
- `updated_at`：文件更新时间
- `sections`：分区数据列表
- `error_message`：读取失败时的错误信息

`sections[].rows` 为前端直接渲染的表格数据。

### `GET /market/push/cards`

用途：一次性返回三类卡片的预览数据。

响应核心字段：

- `cards[].card_type`：`post-close` / `auction` / `intraday`
- `cards[].title`：卡片标题
- `cards[].status`：能力状态
- `cards[].date`：卡片对应交易日
- `cards[].snapshot`：快照数据
- `cards[].card_payload`：飞书卡片 JSON
- `cards[].error_message`：构建失败时的错误信息

## 3. 卡片刷新与发送接口

三类卡片共用两种动作：

- `refresh`：仅刷新快照和卡片内容，不发送
- `send`：构建卡片并直接调用飞书 webhook 发送

支持的卡片类型：

- `post-close`
- `auction`
- `intraday`

### 刷新接口

- `POST /market/push/post-close/refresh`
- `POST /market/push/auction/refresh`
- `POST /market/push/intraday/refresh`

请求体：

```json
{
  "trade_date": "20260413"
}
```

字段说明：

- `trade_date`：可选，不传时由后端按卡片类型自动推断日期

### 发送接口

- `POST /market/push/post-close/send`
- `POST /market/push/auction/send`
- `POST /market/push/intraday/send`

请求体：

```json
{
  "trade_date": "20260413",
  "webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
}
```

字段说明：

- `trade_date`：可选，不传时由后端自动推断
- `webhook`：可选，手动覆盖默认 `FEISHU_BOT_WEBHOOK`

响应核心字段：

- `success`：动作是否成功
- `action`：`refresh` 或 `send`
- `card_type`：卡片类型
- `snapshot`：用于展示的快照数据
- `card_payload`：飞书卡片 JSON
- `send_response`：发送接口返回结果，仅 `send` 动作有值
- `error_message`：失败原因

## 4. 当前前端实际使用的接口

当前 `frontend/src/api/client.js` 已消费这些接口：

- `GET /dashboard/summary`
- `GET /market/history/market-sentiment`
- `GET /market/push/cards`
- `POST /tasks/market-sentiment/run`
- `GET /tasks/market-sentiment/{task_id}`
- `POST /tasks/market-sentiment/{task_id}/cancel`
- `POST /market/push/{cardType}/refresh`
- `POST /market/push/{cardType}/send`

这意味着当前接口文档维护应以后端为主，前端只保留调用层和必要的参数约束，不要在前端再复制一份主文档。

## 5. 文档放置约定

当前项目建议这样放：

1. 主接口文档放 `backend/`
2. 启动方式与后端结构说明放 `backend/README.md`
3. 前端目录只保留接口调用代码和必要联调说明

原因很直接：

- 接口定义源头在后端路由和 schema
- 文档跟着后端放，更新成本最低
- 可以避免前后端各维护一份，最后内容漂移

如果后续接口明显增多，再考虑把接口文档统一收口到仓库根目录 `docs/api/`。当前阶段没有必要单独抽一个重文档目录。

## 6. 当前维护原则

新增或修改接口时，至少同步更新这三处中的两处：

1. 路由与 schema
2. `backend/API_DOCUMENTATION.md`
3. `backend/README.md` 中的能力说明或入口说明

当前阶段不要为了“接口文档平台化”再引入额外工具链。FastAPI 自带 OpenAPI + 一份人工维护 Markdown，已经够用。
