# Backend 说明

这个目录放的是 Kaka_Quant 当前阶段的轻量 FastAPI 封装层。

它的定位不是完整任务平台，而是：

1. 给已有任务提供 HTTP 调用入口。
2. 给前端提供稳定、可消费的读取接口。
3. 在不破坏 Excel 主工作流的前提下，把项目补成一个可联调、可展示的前后端闭环。

## 这个后端现在能做什么

1. 健康检查和任务列表。
2. 触发 `daily-basics` 与 `market-sentiment` 两个历史任务。
3. 让 `market-sentiment` 以后台任务方式运行，并提供状态轮询和取消接口。
4. 给前端返回首页概览数据。
5. 给前端返回 `market-sentiment` 历史数据。
6. 给前端返回三类卡片的快照、刷新结果和发送结果。

## 接口文档在哪看

当前项目接口文档分两类：

1. 仓库内人工维护文档：`backend/API_DOCUMENTATION.md`
2. 测试指导文档：`backend/TESTING_GUIDE.md`
3. FastAPI 自动文档：
   - `http://127.0.0.1:8000/docs`
   - `http://127.0.0.1:8000/redoc`

当前阶段以 `backend/API_DOCUMENTATION.md` 作为主文档入口，Swagger 主要用于联调和临时查看 schema。
如果是第一次接手项目、主要目标是“本地怎么启动、哪些接口能直接测、哪些接口需要外部依赖”，优先看 `backend/TESTING_GUIDE.md`。

## 目录怎么理解

```text
backend/
├── main.py                    # FastAPI 应用入口，同时配置前端本地联调的 CORS
├── api/
│   └── routes.py              # 所有 HTTP 路由集中在这里
├── schemas/
│   ├── tasks.py               # 任务接口的请求/响应模型
│   ├── frontend.py            # 前端消费接口的响应模型
│   └── __init__.py            # schema 导出入口
└── services/
    ├── task_registry.py       # 当前可暴露任务的注册表
    ├── task_runner.py         # 把 API 请求翻译成任务调用
    ├── task_manager.py        # market-sentiment 后台任务管理
    ├── frontend_data.py       # 首页概览、历史数据读取逻辑
    ├── push_cards.py          # 三类卡片的快照、刷新、发送封装
    └── __init__.py            # 服务层导出入口
```

## 小白可以怎么读这套后端

推荐顺序：

1. 先看 `main.py`
   理解 FastAPI 是怎么启动的。
2. 再看 `api/routes.py`
   理解后端到底暴露了哪些接口。
3. 再看 `services/task_manager.py`
   这里最能说明 `market-sentiment` 为什么能后台执行、轮询和取消。
4. 再看 `services/frontend_data.py`
   理解历史页为什么直接读历史主表，而且只取最近 20 个交易日。
5. 最后看 `services/push_cards.py`
   理解三类卡片如何统一刷新与发送。

## 当前主要数据流

### 首页与历史页

1. 前端请求 `/dashboard/summary` 或 `/market/history/market-sentiment`
2. `routes.py` 调到 `frontend_data.py`
3. `frontend_data.py` 识别最新历史主表 `历史数据_起始日期_结束日期.xlsx`
4. 再把前端当前需要的 sheet 和列裁剪成 JSON 返回

### `market-sentiment` 更新任务

1. 前端请求 `POST /tasks/market-sentiment/run`
2. `task_manager.py` 创建后台任务，返回 `task_id`
3. 后台线程执行 `run_market_sentiment.py`
4. 脚本先生成 `补充数据_起始日期_结束日期.xlsx` 到 `storage/backups/`
5. 再把补充数据并回历史主表，并把主表文件名改成新的覆盖区间
6. 前端通过 `GET /tasks/market-sentiment/{task_id}` 轮询状态，必要时调用取消接口

### 卡片页

1. 前端请求 `/market/push/cards` 或具体 refresh/send 接口
2. `routes.py` 调到 `push_cards.py`
3. `push_cards.py` 统一调用 `market/services/` 构造 snapshot
4. 再调用 `market/push_views/` 构造卡片 JSON
5. 如果是发送动作，再通过 `FeishuNotifier` 调 webhook

## 当前接口清单

### 系统与任务

- `GET /health`
- `GET /tasks`
- `POST /tasks/daily-basics/run`
- `POST /tasks/market-sentiment/run`
- `GET /tasks/market-sentiment/{task_id}`
- `POST /tasks/market-sentiment/{task_id}/cancel`

### 前端读取接口

- `GET /dashboard/summary`
- `GET /market/history/market-sentiment`
- `GET /market/push/cards`

### 卡片刷新与发送接口

- `POST /market/push/post-close/refresh`
- `POST /market/push/post-close/send`
- `POST /market/push/auction/refresh`
- `POST /market/push/auction/send`
- `POST /market/push/intraday/refresh`
- `POST /market/push/intraday/send`

## 为什么这样做

因为当前项目阶段的重点是：

- 先把已有链路展示出来
- 先让前端有东西可接
- 不引入数据库和复杂调度系统
- 尽量贴合你真实的 Excel 复盘工作流

所以这里选择：

1. 历史页直接读历史主表 Excel。
2. `market-sentiment` 用轻量后台任务管理，不引入重型队列系统。
3. 卡片页继续复用现有三类卡片逻辑。
4. 发送动作统一走后端，避免前端直接接 webhook 细节。

## 如何启动

在项目根目录安装依赖后运行：

```bash
uvicorn backend.main:app --reload
```

默认地址：

- API 文档：`http://127.0.0.1:8000/docs`
- API 根服务：`http://127.0.0.1:8000`

## 当前注意事项

1. 卡片发送默认读取环境变量或配置里的 `FEISHU_BOT_WEBHOOK`。
2. 盘中卡片可能因为实时权限不足而降级。
3. 历史读取接口依赖当前历史主表已存在；如果没有文件，需要先触发一次 `market-sentiment` 更新任务。
4. 当前仍有一个遗留问题：历史主表更新后，Excel 可能修复 `externalLinks` 缓存，且图表未必自动刷新，详见 `project_memory/decisions/2026-04-02_历史主表更新后Excel外部链接与图表遗留问题.md`。
