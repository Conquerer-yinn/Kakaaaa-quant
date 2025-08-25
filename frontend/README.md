# Frontend 说明

这个目录放的是 Kaka_Quant 当前阶段的 React 前端展示壳。

它不是重后台，也不是任务平台首页，而是优先服务三件事：

1. 把项目讲清楚。
2. 把已经落地的后端能力真实展示出来。
3. 让你 review 时能快速对上页面、接口和数据流。

## 这个前端现在能做什么

1. 首页：展示项目定位、两条主线、当前已落地能力和快捷入口。
2. 历史数据页：只展示 `market-sentiment`，固定读取最新历史主表里的最近 20 个交易日数据。
3. 历史数据页：支持发起 `market-sentiment` 后台更新、轮询状态、请求取消。
4. 推送卡片页：展示盘后、竞价、盘中三类卡片，支持刷新和发送到飞书。
5. 策略页：先做占位说明，不堆假数据。

## 目录怎么理解

```text
frontend/
├── index.html                 # Vite 入口 HTML
├── package.json               # 前端依赖和 npm 脚本
├── package-lock.json          # 前端依赖锁文件
├── vite.config.js             # Vite 开发配置
└── src/
    ├── main.jsx               # React 挂载入口
    ├── App.jsx                # 路由总入口
    ├── styles.css             # 全局样式
    ├── api/
    │   └── client.js          # 所有后端请求统一从这里发出
    ├── components/
    │   ├── Layout.jsx         # 顶部导航和页面外壳
    │   ├── SectionCard.jsx    # 通用内容卡片
    │   ├── StatusBadge.jsx    # 状态标签
    │   ├── MetricGrid.jsx     # 首页概览指标网格
    │   ├── SimpleLineChart.jsx # 早期轻量图表组件，当前首页仍可复用
    │   ├── MetricBarChart.jsx # 历史页柱状图组件
    │   └── DataTable.jsx      # 可点击表头的通用表格
    └── pages/
        ├── HomePage.jsx       # 首页
        ├── HistoryPage.jsx    # 历史数据页
        ├── PushPage.jsx       # 推送卡片页
        └── StrategiesPage.jsx # 策略占位页
```

## 小白可以怎么读这套前端

推荐顺序：

1. 先看 `src/App.jsx`
   这里能看到前端有哪些页面。
2. 再看 `src/api/client.js`
   这里能看到前端到底调了哪些后端接口。
3. 再看 `src/pages/HistoryPage.jsx`
   这里最能体现真实业务数据流，包括后台任务轮询、取消、图表与表格联动。
4. 再看 `src/pages/PushPage.jsx`
   这里能看到卡片预览、刷新、发送是怎么接进来的。
5. 最后看 `src/components/`
   这里是复用组件层，目的是让页面逻辑更容易读。

## 这套前端是怎么做出来的

当前技术选择是：

- React
- React Router
- Vite
- 原生 CSS

这里故意没有上很重的 UI 组件库，原因是：

1. 第一版重点是把页面和后端联调跑通。
2. 当前页面不多，重组件库会增加 review 成本。
3. 这一版更强调数据链路真实，而不是后台框架感。

## 历史页的数据流

历史页现在已经按真实业务收敛：

1. 只读取 `/market/history/market-sentiment`
2. 后端固定返回最近 20 个交易日数据
3. 页面默认选中每个模块的第一项数值列
4. 点击表头里的其他数值列，会切换当前柱状图展示指标
5. 图表和表格共用同一份后端返回数据，不是写死 demo 图
6. 前端不再展示 `daily-basics`
7. 前端也不再展示“位置 / 相对中枢”这类冗余列

## 推送页的数据流

1. 首屏请求 `/market/push/cards`
2. 页面展示三类卡片的状态、快照和卡片载荷
3. 点击刷新会调用 `/market/push/{card_type}/refresh`
4. 点击发送会调用 `/market/push/{card_type}/send`
5. 默认使用后端配置中的 `FEISHU_BOT_WEBHOOK`

## 如何启动

先确保你已经把后端启动好，再在这个目录下运行：

```bash
npm install
npm run dev
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`

如果后端不是跑在默认地址，可以设置环境变量：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 当前注意事项

1. 历史数据页固定读取最新历史主表，而不是测试工作簿或近期临时工作簿。
2. 点击“更新 market-sentiment”时，前端会创建后台任务并轮询状态，再次点击会请求取消。
3. 推送卡片页面默认依赖后端环境变量中的 `FEISHU_BOT_WEBHOOK`。
4. 盘中卡片会受实时权限影响，页面上会明确展示降级说明。
5. 当前仍有一个遗留问题：历史主表更新后，Excel 可能修复 `externalLinks` 缓存，且图表未必自动刷新，详见 `project_memory/decisions/2026-04-02_历史主表更新后Excel外部链接与图表遗留问题.md`。
