const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`);
  }
  return data;
}

export const api = {
  getDashboardSummary() {
    return request("/dashboard/summary");
  },
  getMarketSentimentHistory(limit = 20) {
    return request(`/market/history/market-sentiment?limit=${limit}`);
  },
  getPushCards() {
    return request("/market/push/cards");
  },
};

export { API_BASE_URL };
