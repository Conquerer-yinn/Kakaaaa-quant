from datetime import timedelta

import pandas as pd


HEIGHT_OBSERVATION_COLUMNS = [
    "日期",
    "全市场近十日高度(%)",
    "全市场高度个股",
    "主板近十日高度(%)",
    "主板高度个股",
    "创业板近十日高度(%)",
    "创业板高度个股",
    "最高连板",
]


def build_height_observation_df(all_daily_df, stock_basic_df, trade_dates, market_overview_df):
    # 十日高度表的核心任务，是回答“这一天的十日高度是谁”。
    if all_daily_df.empty:
        return pd.DataFrame(columns=HEIGHT_OBSERVATION_COLUMNS)

    enriched = all_daily_df.copy()
    enriched = enriched.drop(columns=["name", "list_date", "是否ST"], errors="ignore")
    enriched["trade_date"] = pd.to_datetime(enriched["trade_date"], format="%Y%m%d", errors="coerce")
    enriched["close"] = pd.to_numeric(enriched["close"], errors="coerce")
    enriched = enriched.sort_values(["ts_code", "trade_date"])
    # 这里按收盘价计算 10 个交易日累计涨幅。
    enriched["十日涨幅"] = (
        (enriched["close"] / enriched.groupby("ts_code")["close"].shift(10) - 1) * 100
    )

    stock_basic = normalize_stock_basic_df(stock_basic_df, enriched)
    enriched = enriched.merge(stock_basic[["ts_code", "name", "list_date", "是否ST"]], on="ts_code", how="left")

    market_lookup = {}
    if market_overview_df is not None and not market_overview_df.empty:
        market_lookup = market_overview_df.set_index("日期")["最高连板"].to_dict()

    rows = []
    for trade_date in trade_dates:
        trade_dt = pd.to_datetime(trade_date, format="%Y%m%d", errors="coerce")
        if pd.isna(trade_dt):
            continue

        day_df = enriched[enriched["trade_date"] == trade_dt].copy()
        # 跟旧脚本保持一致：排除 ST 和上市未满一年的个股。
        st_mask = day_df["是否ST"].fillna(False).astype(bool)
        day_df = day_df.loc[~st_mask]
        cutoff = trade_dt - timedelta(days=365)
        day_df = day_df[day_df["list_date"].notna() & (day_df["list_date"] <= cutoff)]

        row = {"日期": trade_date, "最高连板": market_lookup.get(trade_date)}
        row.update(extract_height(day_df, "all", "全市场"))
        row.update(extract_height(day_df, "main", "主板"))
        row.update(extract_height(day_df, "chinext", "创业板"))
        rows.append(row)

    return pd.DataFrame(rows, columns=HEIGHT_OBSERVATION_COLUMNS)


