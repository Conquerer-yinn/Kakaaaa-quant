import { Link } from "react-router-dom";

import { SectionCard } from "../components/SectionCard";

export function StrategiesPage() {
  return (
    <div className="page-stack">
      <section className="page-header compact-header">
        <div>
          <p className="eyebrow">策略设计</p>
          <h2>这一页当前先占位，不强行堆假 demo。</h2>
          <p>等策略研究线更成体系后，再补筛选结果、研究记录和日常运行入口。</p>
        </div>
      </section>

      <SectionCard title="为什么先占位" subtitle="当前优先级仍然是把 market 线做深做实。">
        <div className="stack-list">
          <article className="line-card">
            <strong>当前更值得先展示的，是 market 主线</strong>
            <p>因为历史数据链路、消息卡片链路和 API 联调都已经更成熟，前端先接它最容易形成完整闭环。</p>
          </article>
          <article className="line-card">
            <strong>strategies 先保留发展方向</strong>
            <p>后续会逐步补历史样本筛选、Excel 复盘结果、成熟策略的运行登记等内容。</p>
          </article>
        </div>
        <Link className="ghost-button inline-button" to="/">
          回到首页
        </Link>
      </SectionCard>
    </div>
  );
}
