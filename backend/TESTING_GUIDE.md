# Kaka_Quant 后端测试指导

这份文件是给第一次接手这个项目、想用它练习测试的人看的。

先说结论：

1. 这个项目当前**不依赖本地数据库**。
2. 历史数据主要来自 `storage/` 里的 Excel 文件，尤其是 `storage/data_master/`。
3. 如果你把项目连同 `storage/` 一起打包成 zip 发给别人，对方一般可以在本地直接启动后端并完成一部分测试。
4. 但不是所有接口都能离线测试。读 Excel 的接口可以本地直接测；拉行情数据、刷新卡片、发送卡片这类接口还需要外部服务。

## 1. 先理解这个项目怎么“存数据”

当前后端的真实数据来源分两类：

1. 本地 Excel
   目录：`storage/data_master/`、`storage/backups/`
2. 外部服务
   主要是 Tushare 数据接口，以及飞书 webhook

所以测试时要先分清楚：

- **本地只读测试**：不需要数据库，不需要自己先建表，主要验证 API 能不能正常把 Excel 里的内容读出来。
- **任务执行测试**：会去拉外部数据，依赖网络和相关配置。
- **消息发送测试**：除了依赖外部数据，还依赖可用的 webhook。

## 2. 打包给别人之前，要一起带上什么

如果你希望朋友拿到 zip 以后能直接开始测试，建议至少包含这些内容：

1. 整个项目代码。
2. `storage/` 目录。
3. `requirements.txt`。
4. `backend/API_DOCUMENTATION.md`
5. 这份文件 `backend/TESTING_GUIDE.md`

其中最关键的是 `storage/`。没有它，历史数据读取接口虽然能启动，但很可能拿不到可展示内容。

## 3. 哪些接口可以直接本地测试

下面这些接口最适合新手先测：

- `GET /health`
- `GET /tasks`
- `GET /dashboard/summary`
- `GET /market/history/market-sentiment`

原因很简单：

1. `health` 和 `tasks` 主要验证服务有没有起来、任务有没有注册。
2. `dashboard/summary` 返回的是后端整理好的概览信息。
3. `market/history/market-sentiment` 直接读 `storage/data_master/` 里的历史主表 Excel。

这几类接口**不需要本地数据库**。

## 4. 哪些接口不能只靠 zip 离线测

下面这些接口通常不适合“纯离线”测试：

- `POST /tasks/daily-basics/run`
- `POST /tasks/market-sentiment/run`
- `GET /market/push/cards`
- `POST /market/push/{cardType}/refresh`
- `POST /market/push/{cardType}/send`

原因：

1. `daily-basics` 和 `market-sentiment` 会请求外部行情数据。
2. 卡片预览和刷新也会请求外部行情数据。
3. `send` 还会真的调用 webhook。

所以：

- 如果只是练接口测试、联调测试、冒烟测试，先测第 3 节那批接口就够了。
- 如果要测任务执行链路，需要网络、可用的数据源配置，以及不要被 Excel 文件占用。
- 如果要测发送接口，需要一个可用的飞书机器人 webhook。

## 5. 推荐测试顺序

如果对方是第一次接触这个项目，建议按下面顺序来：

1. 先启动后端。
2. 打开 Swagger：`http://127.0.0.1:8000/docs`
3. 先测 `GET /health`
4. 再测 `GET /tasks`
5. 再测 `GET /dashboard/summary`
6. 再测 `GET /market/history/market-sentiment`
7. 确认只读接口都正常以后，再考虑任务执行接口。
8. 最后再测卡片刷新和发送接口。

这个顺序的好处是：先验证“项目能启动、已有 Excel 能读、接口结构没问题”，再进入外部依赖更多的接口。

## 6. 本地启动方式

在项目根目录执行：

```powershell
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

启动后默认访问：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`
- OpenAPI JSON：`http://127.0.0.1:8000/openapi.json`

如果只是做后端接口测试，到这里就够了，不需要先启动前端。

## 7. 新手最适合的测试方法

最推荐直接用 Swagger UI。

原因：

1. 不用自己写请求代码。
2. 可以直接看到接口参数和返回结构。
3. 适合第一次理解这个项目的 API。

### 先做一轮最小冒烟测试

#### 1. `GET /health`

预期：

- 返回 `status: ok`
- 返回服务名
- 返回当前可用任务数量

#### 2. `GET /tasks`

预期：

- 能看到 `daily-basics`
- 能看到 `market-sentiment`

#### 3. `GET /dashboard/summary`

预期：

- 返回项目概览信息
- `success` 为 `true`

#### 4. `GET /market/history/market-sentiment`

推荐先用默认参数，或者 `limit=20`。

预期：

- `success` 为 `true`
- `file_name` 不为空
- `sections` 至少包含：
  - `总市场数据`
  - `高度观察`
  - `创业板专区`

如果这一步成功，说明项目自带的 Excel 数据已经能被后端正确读取。

## 8. 如果要测试任务接口，建议这样测

对于练手的人，我更建议先测 `market-sentiment` 的**测试模式**，不要一上来就改历史主表。

对应接口：

- `POST /tasks/market-sentiment/run`

推荐请求体：

```json
{
  "start_date": "20260320",
  "end_date": "20260402",
  "output_file": null,
  "history": false
}
```

这样做的原因：

1. `history=false` 时更适合生成测试工作簿。
2. 不会把新手第一次练手直接引到“维护历史主表”的路径上。
3. 更容易把这次测试和正式数据区分开。

发起后要继续测试：

1. 记录返回里的 `task_id`
2. 调用 `GET /tasks/market-sentiment/{task_id}` 轮询状态
3. 观察状态是否从 `pending/running` 变成 `succeeded` 或 `failed`

如果中途想测试取消：

1. 先创建一个任务
2. 再调用 `POST /tasks/market-sentiment/{task_id}/cancel`
3. 再轮询状态，看是否进入 `cancelling` 或 `cancelled`

## 9. 卡片接口怎么测

卡片接口分成两类动作：

1. `refresh`：只刷新和生成卡片内容，不发送
2. `send`：真实发送到 webhook

建议测试顺序：

1. 先测 `GET /market/push/cards`
2. 再测 `POST /market/push/post-close/refresh`
3. 确认卡片 JSON 能生成后，再决定要不要测 `send`

不建议新手一开始就测 `send`，因为这会产生真实外部副作用。

## 10. 常见失败原因

### 1. 历史接口返回没有数据

优先检查：

1. zip 里是否带了 `storage/`
2. `storage/data_master/` 下是否存在历史主表 Excel
3. Excel 文件名是否还符合当前项目识别规则，例如 `历史数据_起始日期_结束日期.xlsx`

### 2. 任务接口执行失败

优先检查：

1. 当前机器是否能访问外部行情数据源
2. 相关环境变量或默认配置是否可用
3. 目标 Excel 是否正被打开

Excel 文件如果正开着，写入任务可能失败。

### 3. 卡片接口失败

优先检查：

1. 当前机器是否能访问外部数据接口
2. `trade_date` 是否合理
3. 如果是 `send`，webhook 是否有效

## 11. 给测试同学的最小结论

如果只是想快速练习这个项目的测试：

1. 不要先管数据库，因为这个项目当前没有本地数据库依赖。
2. 先把项目和 `storage/` 一起解压。
3. 先启动后端。
4. 先用 Swagger 测只读接口。
5. 再决定要不要测任务执行和卡片发送。

## 12. 建议你发 zip 前再确认一次

你发给朋友之前，建议自己确认这几件事：

1. `storage/` 已包含进去。
2. `storage/data_master/` 里至少有一份可读的历史主表。
3. `pip install -r requirements.txt` 后能启动 `uvicorn backend.main:app --reload`
4. `GET /market/history/market-sentiment` 能正常返回数据。

如果这四件事成立，对方就比较容易直接上手。

## 13. 一个额外提醒

当前 `common/config.py` 里存在默认外部配置。

如果你只是想让朋友练测试，而不想让他直接使用你现成的外部配置，建议在发 zip 前自行检查这些默认值是否需要清理，避免把真实 token 或 webhook 一起发出去。
