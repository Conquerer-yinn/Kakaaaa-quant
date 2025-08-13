import { useEffect, useState } from "react";

import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";

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
            <div className="timestamp-text">最近日期：{card.date || "-"}</div>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
