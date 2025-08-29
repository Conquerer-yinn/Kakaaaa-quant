# AI 接手说明

这份文件是给任何新 AI 的快速上手入口。

目标：

1. 不依赖某个具体聊天窗口的长期存在。
2. 不依赖某个具体模型的隐性记忆。
3. 让新 AI 在最短时间理解项目并继续工作。

## 推荐阅读顺序

1. `README.md`
2. `backend/README.md`
3. `frontend/README.md`
4. `DEVELOPMENT_PLAN.md`
5. `project_memory/handoff/PROJECT_STATUS.md`
6. `project_memory/handoff/ARCHIVE_RULES.md`
7. `project_memory/decisions/` 中与当前任务最相关的文件
8. 如需完整上下文，再看 `project_memory/chat_archive/`

## 当前最值得优先读的决策文件

1. `project_memory/decisions/2026-04-01_当前阶段FastAPI最小封装原则.md`
2. `project_memory/decisions/2026-04-01_市场卡片推送与三层结构约定.md`
3. `project_memory/decisions/2026-04-02_历史主表更新后Excel外部链接与图表遗留问题.md`
4. `project_memory/decisions/2026-04-02_前后端第一版闭环与文档同步.md`

## 项目核心理解

1. 项目不是一个纯工程化系统，而是服务于个人量化研究工作流。
2. 当前两条主线：
   - `market/`：行情分析、情绪指标、卡片与历史数据
   - `strategies/`：策略研究与后续策略脚本
3. 当前阶段主输出仍然是 Excel。
4. 当前前后端第一版已经落地，但依然坚持轻量边界，不走重平台路线。
5. `market` 下任务当前分成“独立标准任务”和“综合研究任务”两类。

## 重要目录

- `backend/`
  FastAPI 轻量服务层
- `frontend/`
  React 前端展示壳
- `market/jobs/`
  行情任务入口
- `market/indicators/`
  可复用的行情指标与说明
- `project_memory/`
  长期项目记忆、决策、归档、接手说明

## 开发约定

1. 代码尽量简洁、直接、可读。
2. 关键逻辑要有必要的中文短注释，方便 review。
3. 不为了抽象而抽象。
4. 优先考虑维护成本与长期可读性。
5. 形成重要结论后，要同步写入 `project_memory/decisions/` 或 handoff 文件。

## 当前最重要的已落地任务

- `market-sentiment` 历史主表工作流已落地。
- 最小 FastAPI 封装已补齐。
- `market-sentiment` 后台任务管理已落地。
- React 前端第一版已落地。
- 三类飞书卡片的预览、刷新、发送链路已打通。
- 三类卡片已完成真实 webhook 发送联调。

## 当前服务化边界

1. 当前 FastAPI 只做轻量封装层。
2. 当前不做数据库、任务队列、复杂任务状态机。
3. 当前仍以 Excel 为主输出，不因服务化反向改变研究工作流。

## 当前协作方式

1. 主对话窗口负责项目整体设计与全局事务。
2. 子代理负责具体旧脚本迁移、指标开发、策略开发。
3. 重要长期知识必须同步沉淀到仓库，而不是只保留在聊天窗口里。
4. 长期主题窗口的重要原始对话，需要归档到 `project_memory/chat_archive/`。
