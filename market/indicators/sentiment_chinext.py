import pandas as pd

from market.indicators.sentiment_market import count_broken_limit, count_large_retrace


CHINEXT_COLUMNS = [
    "日期",
    "创业板成交额(亿元)",
    "创业板成交额占全市场比重(%)",
    "创业板涨停数",
    "创业板炸板数",
    "创业板大回撤数",
    "创业板连板高度",
    "创业板最高板个股",
    "创业板涨停股平均成交额(亿元)",
    "创业板涨停股平均换手率(%)",
    "创业板涨停股成交额总额(亿元)",
    "创业板最大成交涨停股",
    "创业板最大成交涨停股成交额(亿元)",
]


def build_chinext_row(trade_date, daily_df, daily_basic_df, limit_df, stk_limit_df, total_amount):
    # 创业板专区第一阶段先看三件事：整体温度、涨停股质量、次日反馈样本。
    chinext_daily = ensure_columns(filter_chinext(daily_df), ["ts_code", "amount", "high", "close"])
    chinext_basic = ensure_columns(filter_chinext(daily_basic_df), ["ts_code", "turnover_rate"])
    chinext_limit = ensure_columns(filter_chinext(limit_df), ["ts_code", "limit", "limit_times", "name"])
    chinext_limit_price = ensure_columns(filter_chinext(stk_limit_df), ["ts_code", "up_limit"])

    chinext_amount = round(float(pd.to_numeric(chinext_daily["amount"], errors="coerce").fillna(0).sum()) / 1e5, 2)
    amount_ratio = round(chinext_amount / total_amount * 100, 2) if total_amount else 0.0

    limit_up = chinext_limit[chinext_limit["limit"] == "U"].copy()
    broken_limit = chinext_limit[chinext_limit["limit"] == "Z"].copy()
    broken_count = count_broken_limit(chinext_daily, chinext_limit_price, broken_limit)
    retrace_count = count_large_retrace(chinext_daily)

    daily_amount = chinext_daily[["ts_code", "amount"]].rename(columns={"amount": "daily_amount"})
    merged_limit = limit_up.merge(
        daily_amount,
        on="ts_code",
        how="left",
    ).merge(
        chinext_basic[["ts_code", "turnover_rate"]],
        on="ts_code",
        how="left",
    )

    highest_streak = 0
    highest_streak_name = None
    if not limit_up.empty and "limit_times" in limit_up.columns:
        streaks = pd.to_numeric(limit_up["limit_times"], errors="coerce").fillna(0)
        highest_streak = int(streaks.max())
        highest_names = limit_up.loc[streaks == highest_streak, "name"].dropna().astype(str)
        highest_streak_name = "|".join(highest_names.tolist()) or None

    avg_amount = None
    avg_turnover = None
    total_limit_amount = None
    max_amount_name = None
    max_amount_value = None
    if not merged_limit.empty:
        # 涨停股平均成交额和平均换手率，用来粗看当天强势股质量。
        merged_limit["daily_amount"] = pd.to_numeric(merged_limit["daily_amount"], errors="coerce")
        merged_limit["turnover_rate"] = pd.to_numeric(merged_limit["turnover_rate"], errors="coerce")
        avg_amount = round(float(merged_limit["daily_amount"].mean()) / 1e5, 2)
        avg_turnover = round(float(merged_limit["turnover_rate"].mean()), 2)
        total_limit_amount = round(float(merged_limit["daily_amount"].sum()) / 1e5, 2)

        max_idx = merged_limit["daily_amount"].idxmax()
        if pd.notna(max_idx):
            max_amount_name = merged_limit.loc[max_idx, "name"]
            max_amount_value = round(float(merged_limit.loc[max_idx, "daily_amount"]) / 1e5, 2)

    samples = {
        "limit_up_codes": limit_up["ts_code"].dropna().astype(str).tolist(),
        "broken_codes": build_broken_codes(chinext_daily, chinext_limit_price, broken_limit),
        "core_code": None,
        "core_name": None,
    }
    if not merged_limit.empty:
        # 第一阶段先用创业板涨停股中成交额最大的个股，作为次日核心反馈样本。
        core_idx = merged_limit["daily_amount"].idxmax()
        if pd.notna(core_idx):
            samples["core_code"] = str(merged_limit.loc[core_idx, "ts_code"])
            samples["core_name"] = merged_limit.loc[core_idx, "name"]

    row = {
        "日期": trade_date,
        "创业板成交额(亿元)": chinext_amount,
        "创业板成交额占全市场比重(%)": amount_ratio,
        "创业板涨停数": int(len(limit_up)),
        "创业板炸板数": int(broken_count),
        "创业板大回撤数": int(retrace_count),
        "创业板连板高度": highest_streak,
        "创业板最高板个股": highest_streak_name,
        "创业板涨停股平均成交额(亿元)": avg_amount,
        "创业板涨停股平均换手率(%)": avg_turnover,
        "创业板涨停股成交额总额(亿元)": total_limit_amount,
        "创业板最大成交涨停股": max_amount_name,
        "创业板最大成交涨停股成交额(亿元)": max_amount_value,
    }
    return row, samples


