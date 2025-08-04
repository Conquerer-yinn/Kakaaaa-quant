import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";

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

      <SectionCard title="项目定位" subtitle="当前更像研究工作台，而不是重型量化平台。">
        <p>{summary?.project_positioning || "正在读取项目概览..."}</p>
      </SectionCard>
    </div>
  );
}
