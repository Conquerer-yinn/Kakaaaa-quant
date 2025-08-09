import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { MetricBarChart } from "../components/MetricBarChart";
import { SectionCard } from "../components/SectionCard";

function isNumericColumn(rows, column) {
  if (column === "日期" || column.includes("个股") || column.includes("核心股")) {
    return false;
  }
  return rows.some((row) => row[column] !== null && row[column] !== undefined && !Number.isNaN(Number(row[column])));
}

function buildDefaultMetricMap(sections) {
  const nextMap = {};
  sections.forEach((section) => {
    const metricColumns = section.columns.filter((column) => isNumericColumn(section.rows, column));
    if (metricColumns.length) {
      nextMap[section.key] = metricColumns[0];
    }
  });
  return nextMap;
}

export function HistoryPage() {
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedMetrics, setSelectedMetrics] = useState({});

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const sentimentData = await api.getMarketSentimentHistory(20);
      setMarketSentiment(sentimentData);
      setSelectedMetrics(buildDefaultMetricMap(sentimentData.sections || []));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const historySections = useMemo(() => marketSentiment?.sections || [], [marketSentiment]);

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">指标设计 / 历史数据</p>
          <h2>这一页现在只保留 market-sentiment，并固定展示最近 20 个交易日。</h2>
          <p>图表和表格直接共用同一份真实数据。图表默认显示第一项数值列。</p>
        </div>
      </section>

      {error ? <div className="feedback error">历史数据读取失败：{error}</div> : null}
      {loading ? <div className="feedback info">正在读取最近 20 个交易日数据...</div> : null}

      <div className="grid-two history-grid">
        {historySections.map((section) => {
          const metricColumns = section.columns.filter((column) => isNumericColumn(section.rows, column));
          const activeMetric = selectedMetrics[section.key] || metricColumns[0];
          return (
            <SectionCard
              key={section.key}
              title={section.title}
              subtitle={`展示最近 ${section.rows.length || 0} 个交易日真实数据，默认图表显示第一项数值列。`}
            >
              {activeMetric ? (
                <MetricBarChart
                  title={`${section.title}${activeMetric}`}
                  rows={section.rows}
                  xKey="日期"
                  yKey={activeMetric}
                />
              ) : null}
              <DataTable columns={section.columns} rows={section.rows} />
            </SectionCard>
          );
        })}
      </div>
    </div>
  );
}
