DAILY_BASICS_COLUMNS = [
    "日期",
    "上涨家数",
    "下跌家数",
    "总成交额(亿元)",
    "涨停数",
    "跌停数",
    "最高连板",
    "最高连板个股",
]


def build_daily_basics_row(trade_date, daily_df, limit_df):
    up_count = int((daily_df["pct_chg"] > 0).sum())
    down_count = int((daily_df["pct_chg"] < 0).sum())
    total_amount = round(float(daily_df["amount"].sum()) / 1e5, 2)

    limit_up_count = 0
    limit_down_count = 0
    highest_streak = 0
    highest_streak_stock = None

    if limit_df is not None and not limit_df.empty:
        limit_up_stocks = limit_df[limit_df["limit"] == "U"]
        limit_down_stocks = limit_df[limit_df["limit"] == "D"]

        limit_up_count = len(limit_up_stocks)
        limit_down_count = len(limit_down_stocks)

        if not limit_up_stocks.empty:
            # 用 limit_times 的最大值作为当日最高连板。
            streaks = limit_up_stocks["limit_times"].fillna(0).astype(int)
            max_idx = streaks.idxmax()
            highest_streak = int(streaks.loc[max_idx])
            highest_streak_stock = limit_up_stocks.loc[max_idx, "name"]

    return {
        "日期": str(trade_date),
        "上涨家数": up_count,
        "下跌家数": down_count,
        "总成交额(亿元)": total_amount,
        "涨停数": limit_up_count,
        "跌停数": limit_down_count,
        "最高连板": highest_streak,
        "最高连板个股": highest_streak_stock,
    }

