import { useEffect, useState } from "react";

import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { SectionCard } from "../components/SectionCard";

export function HistoryPage() {
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const sentimentData = await api.getMarketSentimentHistory(20);
      setMarketSentiment(sentimentData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">指标设计 / 历史数据</p>
          <h2>这一页现在只保留 market-sentiment，并固定展示最近 20 个交易日。</h2>
          <p>图表和表格直接共用同一份真实数据。</p>
        </div>
      </section>

      {error ? <div className="feedback error">历史数据读取失败：{error}</div> : null}
      {loading ? <div className="feedback info">正在读取最近 20 个交易日数据...</div> : null}

      <div className="grid-two history-grid">
        {(marketSentiment?.sections || []).map((section) => (
          <SectionCard
            key={section.key}
            title={section.title}
            subtitle={`展示最近 ${section.rows.length || 0} 个交易日真实数据。`}
          >
            <DataTable columns={section.columns} rows={section.rows} />
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
