import { useEffect, useState } from "react";

import { api } from "../api/client";
import { MetricGrid } from "../components/MetricGrid";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";

const CARD_ENDPOINT_KEY = {
  "post-close": "post-close",
  auction: "auction",
  intraday: "intraday",
};

const CARD_METRICS = {
  "post-close": [
    ["日期", "date"],
    ["总成交额", "total_turnover"],
    ["涨停数", "limit_up_count"],
    ["炸板数", "broken_limit_count"],
    ["最高连板", "highest_streak"],
    ["创业板占比", "chinext_turnover_ratio"],
  ],
  auction: [
    ["日期", "date"],
    ["推送时点", "time_point"],
    ["竞价成交额", "auction_turnover_yi"],
    ["竞价涨停数", "limit_up_count"],
    ["竞价跌停数", "limit_down_count"],
    ["创业板开盘涨幅", "chinext_index_pct"],
  ],
  intraday: [
    ["日期", "date"],
    ["推送时点", "time_point"],
    ["预计成交额", "estimated_turnover_yi"],
    ["上涨家数", "up_count"],
    ["跌停家数", "limit_down_count"],
    ["炸板数", "broken_limit_count"],
  ],
};

function buildMetricItems(card) {
  return (CARD_METRICS[card.card_type] || []).map(([label, key]) => ({
    label,
    value: card.snapshot?.[key] ?? card.date ?? "-",
  }));
}

export function PushPage() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState("");

  const loadCards = async () => {
    setLoading(true);
    try {
      const result = await api.getPushCards();
      setCards(result.cards || []);
    } catch (err) {
      setFeedback(`卡片读取失败：${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCards();
  }, []);

  const handleAction = async (cardType, action) => {
    setFeedback("");
    try {
      const result =
        action === "refresh"
          ? await api.refreshPushCard(CARD_ENDPOINT_KEY[cardType])
          : await api.sendPushCard(CARD_ENDPOINT_KEY[cardType]);
      setFeedback(
        result.success
          ? `${result.title} ${action === "refresh" ? "刷新成功" : "发送成功"}`
          : `${result.title} ${action === "refresh" ? "刷新失败" : "发送失败"}：${result.error_message}`
      );
      await loadCards();
    } catch (err) {
      setFeedback(err.message);
    }
  };

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">指标设计 / 推送数据</p>
          <h2>三类卡片统一放在一个页面里，方便演示也方便后续继续扩展。</h2>
          <p>页面直接对接后端快照接口与发送接口，不反向依赖 Excel。</p>
        </div>
      </section>

      {feedback ? <div className="feedback info">{feedback}</div> : null}
      {loading ? <div className="feedback info">正在读取卡片快照...</div> : null}

      <div className="stack-list">
        {cards.map((card) => (
          <SectionCard
            key={card.card_type}
            title={card.title}
            subtitle={card.error_message || card.snapshot?.availability_note || "当前卡片可用于展示与手动触发发送。"}
            action={<StatusBadge status={card.status} label={card.status_label} />}
          >
            <div className="row-between mobile-stack">
              <div className="button-row compact">
                <button className="primary-button" onClick={() => handleAction(card.card_type, "refresh")}>
                  刷新最新内容
                </button>
                <button className="ghost-button" onClick={() => handleAction(card.card_type, "send")}>
                  发送到飞书
                </button>
              </div>
              <div className="timestamp-text">最近日期：{card.date || "-"}</div>
            </div>

            <MetricGrid items={buildMetricItems(card)} />

            {card.snapshot?.summary_text ? (
              <div className="text-panel">
                <strong>情绪结论</strong>
                <p>{card.snapshot.summary_text}</p>
              </div>
            ) : null}

            {card.snapshot?.risk_text ? (
              <div className="text-panel muted">
                <strong>风险提示</strong>
                <p>{card.snapshot.risk_text}</p>
              </div>
            ) : null}

            {card.snapshot?.availability_note ? (
              <div className="text-panel muted">
                <strong>当前说明</strong>
                <p>{card.snapshot.availability_note}</p>
              </div>
            ) : null}

            <details className="json-panel">
              <summary>查看卡片 JSON 预览</summary>
              <pre>{JSON.stringify(card.card_payload || {}, null, 2)}</pre>
            </details>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
