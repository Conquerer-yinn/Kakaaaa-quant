import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";

export function StrategiesPage() {
  const [strategies, setStrategies] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getStrategies()
      .then((result) => setStrategies(result.strategies || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-stack">
      <section className="page-header compact-header">
        <div>
          <p className="eyebrow">策略设计</p>
          <h2>策略注册表直接映射到这一页，研究进展一目了然。</h2>
          <p>是否纳入日常运行、是否推送摘要，都由 strategies/strategy_registry.yaml 控制。</p>
        </div>
      </section>

      {error ? <div className="feedback error">策略注册表读取失败：{error}</div> : null}
      {loading ? <div className="feedback info">正在读取策略注册表...</div> : null}

      <SectionCard title="已登记策略" subtitle="启用状态与推送开关来自注册表真实配置。">
        <div className="stack-list">
          {strategies.map((strategy) => (
            <article key={strategy.name} className="line-card">
              <div className="row-between">
                <strong>{strategy.name}</strong>
                <StatusBadge
                  status={strategy.enabled ? "stable" : "planning"}
                  label={strategy.enabled ? "日常运行中" : "研究阶段"}
                />
              </div>
              <p>脚本：{strategy.script}</p>
              <p>
                推送摘要：{strategy.push ? "开启" : "关闭"}
                {strategy.notes ? `　·　笔记：${strategy.notes}` : ""}
              </p>
            </article>
          ))}
          {!loading && !strategies.length && !error ? (
            <article className="line-card">
              <strong>注册表当前为空</strong>
              <p>在 strategies/ 目录添加策略脚本并登记到 strategy_registry.yaml 后，这里会自动展示。</p>
            </article>
          ) : null}
        </div>
        <Link className="ghost-button inline-button" to="/">
          回到首页
        </Link>
      </SectionCard>
    </div>
  );
}
