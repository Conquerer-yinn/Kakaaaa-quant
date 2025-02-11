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
