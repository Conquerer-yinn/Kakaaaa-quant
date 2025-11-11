# 安全与配置说明

## 凭据管理原则

1. 所有凭据只从环境变量读取（见 `common/config.py`），仓库中不保存任何真实凭据。
2. `.env` 已加入 `.gitignore`；`.env.example` 只保存字段名和占位值。
3. 历史上如果某个 Token / Webhook 曾出现在提交、日志或文档中，一律视为已泄露，立即轮换。

## 涉及的凭据清单

| 配置项 | 用途 | 泄露影响 | 轮换方式 |
| --- | --- | --- | --- |
| `TUSHARE_TOKEN` | 行情数据接口 | 他人消耗你的积分与频次配额 | tushare.pro 个人中心重置 |
| `FEISHU_BOT_WEBHOOK` | 飞书群机器人推送 | 任何人可向群里发消息 | 飞书群机器人设置中删除重建 |
| `DINGDING_WEBHOOK` | 钉钉推送（可选） | 同上 | 钉钉群机器人重建 |
| `WENCAI_COOKIE` | 问财查询（可选） | 会话冒用 | 重新登录获取 |

## 本地配置方式

```bash
cp .env.example .env
# 编辑 .env 填入真实值；uvicorn / 任务脚本会自动从环境读取
```

Windows PowerShell 临时设置：

```powershell
$env:TUSHARE_TOKEN = "..."
$env:FEISHU_BOT_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/..."
```

## 提交前自查

1. `git diff` 里不允许出现 `open-apis/bot/v2/hook/` 后带真实 ID 的 URL。
2. 不允许出现 32 位以上的十六进制 Token 字面量。
3. 聊天记录归档进 `project_memory/chat_archive/` 前，先把凭据替换为 `<REDACTED>` 占位。
