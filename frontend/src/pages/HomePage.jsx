import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";

export function HomePage() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api
      .getDashboardSummary()
      .then(setSummary)
      .catch(() => {});
  }, []);

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">项目展示版前端</p>
          <h2>先把项目讲清楚，再逐步把研究动作搬到页面里。</h2>
          <p className="hero-text">
            这一版不做重后台，而是围绕真实工作流，把历史数据、消息卡片和项目定位整理成一个可演示、可讲述、可联调的前端壳。
          </p>
        </div>
        <div className="hero-actions">
          <Link className="primary-button" to="/market/history">
            查看历史数据
          </Link>
          <Link className="ghost-button" to="/market/push">
            查看推送卡片
          </Link>
        </div>
      </section>

      <div className="grid-two">
        <SectionCard title="项目定位" subtitle="当前更像研究工作台，而不是重型量化平台。">
          <p>{summary?.project_positioning || "正在读取项目概览..."}</p>
        </SectionCard>
        <SectionCard title="快速入口" subtitle="优先展示最能说明项目价值的两个页面。">
          <div className="link-grid">
            {(summary?.quick_links || []).map((link) => (
              <Link key={link.path} to={link.path} className="quick-link-card">
                <strong>{link.label}</strong>
                <span>{link.description}</span>
              </Link>
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="grid-two">
        <SectionCard title="两条主线" subtitle="项目目前围绕 market 与 strategies 组织。">
          <div className="stack-list">
            {(summary?.main_lines || []).map((line) => (
              <article key={line.title} className="line-card">
                <strong>{line.title}</strong>
                <p>{line.description}</p>
              </article>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="当前已落地能力" subtitle="先把真实链路展示出来，再逐步扩展页面。">
          <div className="stack-list">
            {(summary?.capability_summary || []).map((item) => (
              <article key={item.title} className="capability-card">
                <div className="row-between">
                  <strong>{item.title}</strong>
                  <StatusBadge status={item.status} />
                </div>
                <p>{item.description}</p>
              </article>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
