# Kaka_Quant

Kaka_Quant 是一个面向 A 股研究工作流的个人量化研究工作台。

它不是重型量化平台，也不是纯前端展示项目，而是围绕你真实会用到的研究流程，逐步把这些能力接起来：

- Excel 历史复盘
- FastAPI 任务封装
- React 前端展示
- 飞书消息卡片
- 项目记忆与协作沉淀

## 当前项目定位

当前项目分两条主线：

1. `market/`
   行情分析、市场情绪、盘中盘后辅助判断、消息卡片。
2. `strategies/`
   策略研究、历史筛选、Excel 复盘，以及后续成熟策略的日常运行。

当前阶段仍然以 Excel 为主输出，但前后端第一版已经补齐，项目已经具备“可运行、可展示、可讲述”的完整外壳。

## 当前整体结构

```text
Kaka_Quant/
├── backend/                       # FastAPI 轻量服务层
├── common/                        # 配置、通知、通用工具
├── data_engine/                   # 数据获取与 API 封装
├── frontend/                      # React + Vite 前端展示壳
├── market/                        # 行情任务、指标、服务、卡片视图
├── project_memory/                # 长期决策、状态、归档与接手说明
├── storage/                       # Excel 主表、备份、输出文件
├── strategies/                    # 策略研究与后续策略脚本
├── DEVELOPMENT_PLAN.md
├── 前端开发计划.md
├── 后端开发计划.md
├── 补充开发计划.md
└── README.md
```

## 当前已经落地的核心能力

### 1. `market-sentiment` 历史主表工作流

`market-sentiment` 已经切换成真实可持续维护的历史主表模式：

- 历史主表命名规则：`历史数据_起始日期_结束日期.xlsx`
- 每次补数先生成：`补充数据_起始日期_结束日期.xlsx`
- 补充数据写入 `storage/backups/`
- 随后并回历史主表，并更新主表文件名覆盖区间
- 测试运行统一输出：`测试数据_起始日期_结束日期.xlsx`

前端历史页固定读取最新历史主表里的最近 20 个交易日数据，不再单独展示 `daily-basics`。

### 2. FastAPI 轻量服务层

当前后端已经具备这些接口：

#### 系统与任务

- `GET /health`
- `GET /tasks`
- `POST /tasks/daily-basics/run`
- `POST /tasks/market-sentiment/run`
- `GET /tasks/market-sentiment/{task_id}`
- `POST /tasks/market-sentiment/{task_id}/cancel`

#### 前端读取接口

- `GET /dashboard/summary`
- `GET /market/history/market-sentiment`
- `GET /market/push/cards`

#### 卡片刷新与发送接口

- `POST /market/push/post-close/refresh`
- `POST /market/push/post-close/send`
- `POST /market/push/auction/refresh`
- `POST /market/push/auction/send`
- `POST /market/push/intraday/refresh`
- `POST /market/push/intraday/send`

### 3. React 前端第一版

前端当前页面包括：

- `/` 项目首页
- `/market/history` 历史数据页
- `/market/push` 推送卡片页
- `/strategies` 策略占位页

当前前端重点：

- 历史页只展示 `market-sentiment`
- 图表与表格共用同一份真实数据
- 图表默认显示第一项数值列
- 点击表头里的数值列，可切换当前柱状图展示指标
- 历史页支持发起 `market-sentiment` 后台任务，并轮询状态、请求取消
- 推送页支持盘后、竞价、盘中三类卡片的预览、刷新、发送

### 4. 三类飞书卡片

当前已经接通三类卡片：

- 盘后复盘卡片
- 竞价观察卡片
- 盘中节奏卡片

当前状态：

- 盘后卡片：稳定可用
- 竞价卡片：第一版可用
- 盘中卡片：实验性，允许因实时权限不足而降级

本地真实联调状态：

- 盘后卡片发送成功
- 竞价卡片发送成功
- 盘中卡片发送成功

卡片当前直接基于原始数据层和指标计算层生成，不再反向依赖 Excel 视图层。

## 如何启动项目

推荐按“后端 -> 前端”的顺序启动。

### 1. 安装 Python 依赖

在项目根目录运行：

```bash
pip install -r requirements.txt
```

### 2. 确认关键配置

当前项目至少依赖这些配置：

- `TUSHARE_TOKEN`
- `FEISHU_BOT_WEBHOOK`
- 可选：`TUSHARE_REQUEST_DELAY`

目前项目把默认配置写在 [`common/config.py`](./common/config.py) 中；如果后续要切换到 `.env` 方案，也建议保持字段名一致。

### 3. 启动后端

在项目根目录运行：

```bash
uvicorn backend.main:app --reload
```

默认地址：

- API 根地址：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`

### 4. 启动前端

进入前端目录：

```bash
cd frontend
npm install
npm run dev
```

默认地址：

- 前端页面：`http://127.0.0.1:5173`

如果后端不在默认地址，可设置：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```
