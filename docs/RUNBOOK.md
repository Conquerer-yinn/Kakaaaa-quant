# 运行手册

日常使用的完整操作清单。前置：Python 3.12+、Node 20+，并按 `docs/SECURITY.md` 配好环境变量。

## 1. 安装依赖

```bash
pip install -r requirements.txt -r requirements-dev.txt
cd frontend && npm ci
```

## 2. 行情任务

```bash
# 每日基础数据：首次初始化
python market/jobs/run_daily_basics.py --start-date 20260101 --end-date 20260301
# 之后日常增量
python market/jobs/run_daily_basics.py

# 市场情绪历史主表：日常增量
python market/jobs/run_market_sentiment.py
# 测试模式（不动主表）
python market/jobs/run_market_sentiment.py --test-mode --start-date 20260201
```

## 3. 飞书卡片

```bash
python market/jobs/push_post_close_card.py --trade-date 20260301 --dry-run   # 预览
python market/jobs/push_post_close_card.py --trade-date 20260301             # 发送
python market/jobs/push_auction_card.py --dry-run
python market/jobs/push_intraday_card.py --dry-run
```

## 4. 前后端

```bash
uvicorn backend.main:app --reload          # API: http://127.0.0.1:8000/docs
cd frontend && npm run dev                 # 页面: http://127.0.0.1:5173
```

## 5. 策略

```bash
python strategies/run_strategies.py --all              # 查看注册表
python strategies/run_strategies.py --trade-date 20260301
python strategies/example_strategy.py                  # 单策略手动跑
```

## 6. 测试与检查

```bash
pytest              # 后端与指标全量测试
ruff check .        # 语法级静态检查
cd frontend && npm run build   # 前端构建冒烟
```

## 7. Docker（可选）

```bash
docker compose up --build
# backend: http://127.0.0.1:8000  frontend: http://127.0.0.1:5173
```

## 常见问题

1. **Tushare 限流**：`data_engine` 已带指数退避重试；仍然失败时把 `TUSHARE_REQUEST_DELAY` 调大到 1 以上。
2. **Excel 写入 PermissionError**：目标工作簿正被 Excel 打开，关掉后重跑即可，历史数据已自动备份。
3. **前端读不到数据**：确认后端已启动，且 `VITE_API_BASE_URL` 指向正确地址。
