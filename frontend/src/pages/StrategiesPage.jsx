import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { MetricGrid } from "../components/MetricGrid";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { STUDY_BADGE, buildStrategyMetrics } from "./strategyViewModel";


export function StrategiesPage() {
  const [study, setStudy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [registry, setRegistry] = useState([]);

  const loadStudy = async () => {
    setLoading(true);
    setError("");
    try {
      setStudy(await api.getChinextLimitUpStudy(100));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudy();
  }, []);

  useEffect(() => {
    api
      .getStrategies()
      .then((result) => setRegistry(result.strategies || []))
      .catch(() => {});
  }, []);

  const runStudy = async () => {
    setRunning(true);
    setError("");
    try {
      setStudy(await api.runChinextLimitUpStudy());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRunning(false);
    }
  };

  const metrics = useMemo(
    () => buildStrategyMetrics(study?.metadata || {}),
    [study?.metadata],
  );
  const summaryColumns = study?.summary?.length ? Object.keys(study.summary[0]) : [];
  const groupColumns = study?.group_summary?.length ? Object.keys(study.group_summary[0]) : [];
  const qualityColumns = study?.quality_summary?.length ? Object.keys(study.quality_summary[0]) : [];

  return (
    <div className="page-stack">
      <section className="page-header strategy-header">
        <div>
          <p className="eyebrow">策略研究 · 第一条真实闭环</p>
          <h2>创业板涨停后 5 日事件研究</h2>
          <p>识别创业板涨停样本，观察事件后第 1、3、5 个交易日相对创业板指数的表现，并沉淀为可复盘 Excel。</p>
        </div>
        <button className="primary-button" type="button" onClick={runStudy} disabled={running || loading}>
          {running ? "研究运行中…" : "运行最近 120 天研究"}
        </button>
      </section>

      <div className="feedback info strategy-disclaimer">
        <strong>研究边界：</strong>
        这里展示的是历史事件与相对 399006.SZ 的超额收益统计，不包含交易成本、滑点、仓位或盘中成交模拟，也不代表策略已经验证盈利。
      </div>

      {loading ? <div className="feedback info">正在读取最新策略研究结果…</div> : null}
      {error ? <div className="feedback error">{error}</div> : null}

      {!loading && study?.success ? (
        <>
          <SectionCard
            title="研究概览"
            subtitle={`结果文件：${study.file_name || "-"} · 更新时间：${study.updated_at || "-"}`}
            action={<StatusBadge status={STUDY_BADGE.status} label={STUDY_BADGE.label} />}
          >
            <MetricGrid items={metrics} />
            <div className="research-definition-grid">
              <article className="text-panel muted">
                <strong>事件定义</strong>
                <p>股票代码以 300/301 开头，且 Tushare 涨跌停明细标记为涨停。</p>
              </article>
              <article className="text-panel muted">
                <strong>完整样本</strong>
                <p>事件日有有效收盘价，并且事件后存在完整 5 个交易日行情。</p>
              </article>
              <article className="text-panel muted">
                <strong>收益口径</strong>
                <p>以事件日收盘价为基准，计算未来第 1、3、5 个交易日的收盘收益。</p>
              </article>
              <article className="text-panel muted">
                <strong>基准与分组</strong>
                <p>使用 399006.SZ 计算超额收益，并按首板/连板和事件日市场环境分组。</p>
              </article>
            </div>
          </SectionCard>

          <SectionCard title="总体周期统计" subtitle="个股收益、基准收益、超额收益及正收益比例。">
            <DataTable columns={summaryColumns} rows={study.summary || []} />
          </SectionCard>

          <SectionCard title="分组统计" subtitle="分别比较首板/连板与弱/中/强市场环境。">
            <DataTable columns={groupColumns} rows={study.group_summary || []} />
          </SectionCard>

          <SectionCard title="样本质量" subtitle="所有排除项和缺失项显式计数，不静默丢弃。">
            <DataTable columns={qualityColumns} rows={study.quality_summary || []} />
          </SectionCard>

          <SectionCard title="最近事件样本" subtitle="默认展示工作簿中最近 100 条完整事件。">
            <DataTable columns={study.detail_columns || []} rows={study.details || []} />
          </SectionCard>
        </>
      ) : null}

      {!loading && study && !study.success ? (
        <SectionCard title="尚无研究结果" subtitle="首次运行会拉取真实 Tushare 数据并生成 Excel。">
          <div className="empty-block">{study.error_message || "当前没有可展示的数据。"}</div>
        </SectionCard>
      ) : null}

      <SectionCard title="已登记策略" subtitle="是否纳入日常运行由 strategies/strategy_registry.yaml 控制。">
        <div className="stack-list">
          {registry.map((strategy) => (
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
          {!registry.length ? (
            <article className="line-card">
              <strong>注册表当前为空</strong>
              <p>在 strategies/ 目录添加策略脚本并登记到 strategy_registry.yaml 后，这里会自动展示。</p>
            </article>
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}
