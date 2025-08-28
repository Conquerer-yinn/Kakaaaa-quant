# 统一归档规则

这份文件用于约定：以后不管在哪个对话窗口、用哪个模型、在哪个 team 中推进项目，都按同一套方式归档。

## 归档目标

1. 让长期项目知识脱离聊天平台本身
2. 让任何新 AI 都能快速理解项目
3. 让项目切换模型、账号、workspace 时仍可持续推进

## 四类文件

### 1. 原始对话全文

放在：`project_memory/chat_archive/`

用途：
- 保存重要主对话的原始全文或接近全文的重建稿
- 尽可能保留上下文和讨论过程

命名建议：
- `YYYY-MM-DD_主题_原始全文.md`

### 2. 结构化决策

放在：`project_memory/decisions/`

用途：
- 保存整理后的结论
- 保存项目规则、目录约定、设计共识

命名建议：
- `YYYY-MM-DD_决策主题.md`

### 3. 当前项目状态

放在：`project_memory/handoff/PROJECT_STATUS.md`

用途：
- 给未来任何 AI 或人一个最快的当前项目入口
- 说明现在做到哪里、卡在哪里、下一步干什么

### 4. AI 接手说明

放在：`project_memory/handoff/AI_HANDOFF.md`

用途：
- 告诉新 AI 先看哪些文件
- 告诉新 AI 这个项目有哪些长期约定

## 推荐工作流程

### 日常对话后

1. 如果对话很重要，把原始聊天归档到 `chat_archive/`
2. 如果形成了明确结论，把结论写入 `decisions/`
3. 如果项目状态发生变化，更新 `PROJECT_STATUS.md`

### 新 AI 接手时

建议阅读顺序：

1. `README.md`
2. `DEVELOPMENT_PLAN.md`
3. `project_memory/handoff/PROJECT_STATUS.md`
4. `project_memory/handoff/AI_HANDOFF.md`
5. `project_memory/decisions/` 中最相关的文件
6. 必要时再看 `chat_archive/`

## 核心原则

1. 不依赖某个平台的聊天记录长期可访问。
2. 不依赖某个模型的长期记忆能力。
3. 真正长期有效的知识，必须进入仓库。