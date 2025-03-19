import pandas as pd


MARKET_OVERVIEW_COLUMNS = [
    "日期",
    "上涨家数",
    "下跌家数",
    "总成交额(亿元)",
    "涨停数",
    "跌停数",
    "炸板数",
    "大回撤数",
    "最高连板",
    "最高连板个股",
]


def build_market_overview_row(trade_date, daily_df, limit_df, stk_limit_df):
    # 总市场表负责聚合盘后最常看的基础情绪指标。
    normalized_daily = normalize_daily_df(daily_df)
    normalized_limit = normalize_limit_df(limit_df)
    normalized_limit_price = normalize_limit_price_df(stk_limit_df)

    up_count = int((normalized_daily["pct_chg"] > 0).sum())
    down_count = int((normalized_daily["pct_chg"] < 0).sum())
    total_amount = round(float(normalized_daily["amount"].fillna(0).sum()) / 1e5, 2)

    limit_up_stocks = normalized_limit[normalized_limit["limit"] == "U"]
    limit_down_stocks = normalized_limit[normalized_limit["limit"] == "D"]
    broken_limit_stocks = normalized_limit[normalized_limit["limit"] == "Z"]
    broken_limit_count = count_broken_limit(normalized_daily, normalized_limit_price, broken_limit_stocks)
    retrace_count = count_large_retrace(normalized_daily)

    highest_streak = 0
    highest_streak_stock = None
    if not limit_up_stocks.empty and "limit_times" in limit_up_stocks.columns:
        # limit_times 直接使用 Tushare 连板数字段。
        streaks = pd.to_numeric(limit_up_stocks["limit_times"], errors="coerce").fillna(0)
        highest_streak = int(streaks.max())
        highest_names = limit_up_stocks.loc[streaks == highest_streak, "name"].dropna().astype(str)
        highest_streak_stock = "|".join(highest_names.tolist()) or None

    return {
        "日期": str(trade_date),
        "上涨家数": up_count,
        "下跌家数": down_count,
        "总成交额(亿元)": total_amount,
        "涨停数": int(len(limit_up_stocks)),
        "跌停数": int(len(limit_down_stocks)),
        "炸板数": int(broken_limit_count),
        "大回撤数": int(retrace_count),
        "最高连板": highest_streak,
        "最高连板个股": highest_streak_stock,
    }


