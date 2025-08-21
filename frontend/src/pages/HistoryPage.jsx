import { useEffect, useMemo, useRef, useState } from "react";

import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { MetricBarChart } from "../components/MetricBarChart";
import { SectionCard } from "../components/SectionCard";

const ACTIVE_TASK_STATUSES = new Set(["pending", "running", "cancelling"]);

function formatTaskResultMessage(task) {
  const result = task?.result;
  if (!result) {
    return "";
  }
  if (task?.status === "succeeded") {
    return result.success
      ? `${result.task_name} 已执行完成，输出目标：${result.output_target}`
      : `${result.task_name} 已执行完成：${result.error_message || "任务未产生新数据。"}`;
  }
  return `${result.task_name} 执行失败：${result.error_message || "未知错误"}`;
}

function formatTaskStatusMessage(task) {
  if (!task) {
    return "";
  }
  if (task.progress_message) {
    return task.progress_message;
  }
  if (task.status === "cancelled") {
    return "market-sentiment 更新已取消。";
  }
  if (task.status === "failed") {
    return task.error_message || "market-sentiment 执行失败。";
  }
  return `market-sentiment 当前状态：${task.status}`;
}

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
  const [actionMessage, setActionMessage] = useState("");
  const [error, setError] = useState("");
  const [selectedMetrics, setSelectedMetrics] = useState({});
  const [marketTask, setMarketTask] = useState(null);
  const handledTerminalTaskRef = useRef("");

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

  const isTaskActive = marketTask ? ACTIVE_TASK_STATUSES.has(marketTask.status) : false;

  useEffect(() => {
    if (!marketTask?.task_id || !ACTIVE_TASK_STATUSES.has(marketTask.status)) {
      return undefined;
    }

    const timer = window.setInterval(async () => {
      try {
        const nextTask = await api.getMarketSentimentTask(marketTask.task_id);
        setMarketTask(nextTask);
      } catch (err) {
        setActionMessage(err.message);
      }
    }, 1500);

    return () => window.clearInterval(timer);
  }, [marketTask?.task_id, marketTask?.status]);

  useEffect(() => {
    if (!marketTask?.task_id || ACTIVE_TASK_STATUSES.has(marketTask.status)) {
      return;
    }

    const handledKey = `${marketTask.task_id}:${marketTask.status}`;
    if (handledTerminalTaskRef.current === handledKey) {
      return;
    }
    handledTerminalTaskRef.current = handledKey;

    const finalizeTask = async () => {
      const nextMessage = marketTask.result ? formatTaskResultMessage(marketTask) : formatTaskStatusMessage(marketTask);
      setActionMessage(nextMessage);
      if (marketTask.status === "succeeded") {
        await loadData();
      }
    };

    finalizeTask();
  }, [marketTask]);

  const handleRunMarketSentiment = async () => {
    try {
      if (isTaskActive && marketTask?.task_id) {
        const cancelledTask = await api.cancelMarketSentimentTask(marketTask.task_id);
        setMarketTask(cancelledTask);
        setActionMessage(formatTaskStatusMessage(cancelledTask));
        return;
      }

      const nextTask = await api.startMarketSentimentTask();
      setMarketTask(nextTask);
      setActionMessage(
        nextTask.created
          ? "market-sentiment 已加入后台执行，正在轮询任务状态。"
          : "已有 market-sentiment 任务正在执行，已重新连接到当前任务。",
      );
    } catch (err) {
      setActionMessage(err.message);
    }
  };

  const historySections = useMemo(() => marketSentiment?.sections || [], [marketSentiment]);

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">指标设计 / 历史数据</p>
          <h2>这一页现在只保留 market-sentiment，并固定展示最近 20 个交易日。</h2>
          <p>图表和表格直接共用同一份真实数据。点击表头里的数值列，就能切换当前柱状图展示内容。</p>
        </div>
        <div className="button-row">
          <button className={`primary-button${isTaskActive ? " danger-button" : ""}`} onClick={handleRunMarketSentiment}>
            {isTaskActive ? "暂停更新" : "更新 market-sentiment"}
          </button>
        </div>
      </section>

      {actionMessage ? <div className="feedback info">{actionMessage}</div> : null}
      {marketTask ? (
        <div className="feedback info">
          当前任务状态：{marketTask.status}
          {marketTask.cancel_requested ? "，已请求取消" : ""}
        </div>
      ) : null}
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
              <DataTable
                columns={section.columns}
                rows={section.rows}
                activeColumn={activeMetric}
                interactiveColumns={metricColumns}
                onHeaderClick={(column) =>
                  setSelectedMetrics((current) => ({
                    ...current,
                    [section.key]: column,
                  }))
                }
              />
            </SectionCard>
          );
        })}
      </div>
    </div>
  );
}

