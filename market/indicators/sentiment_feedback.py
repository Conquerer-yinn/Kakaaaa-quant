import pandas as pd


CHINEXT_FEEDBACK_COLUMNS = [
    "日期",
    "昨日创业板涨停样本数",
    "昨日创业板涨停股次日开盘溢价(%)",
    "昨日创业板涨停股次日收盘溢价(%)",
    "昨日创业板炸板样本数",
    "昨日创业板炸板股次日开盘溢价(%)",
    "昨日创业板炸板股次日收盘溢价(%)",
    "昨日创业板核心股",
    "昨日创业板核心股次日开盘溢价(%)",
    "昨日创业板核心股次日盘中最高涨幅(%)",
    "昨日创业板核心股次日收盘涨幅(%)",
]


def build_chinext_feedback_rows(trade_dates, daily_by_date, samples_by_date):
    # 次日反馈表统一按“昨日样本 -> 今日表现”的顺序构建。
    rows = []
    previous_date = None

    for trade_date in trade_dates:
        current_daily = normalize_daily_df(daily_by_date.get(trade_date))
        previous_samples = samples_by_date.get(previous_date) if previous_date else None

        row = {
            "日期": trade_date,
            "昨日创业板涨停样本数": 0,
            "昨日创业板涨停股次日开盘溢价(%)": 0.0,
            "昨日创业板涨停股次日收盘溢价(%)": 0.0,
            "昨日创业板炸板样本数": 0,
            "昨日创业板炸板股次日开盘溢价(%)": 0.0,
            "昨日创业板炸板股次日收盘溢价(%)": 0.0,
            "昨日创业板核心股": None,
            "昨日创业板核心股次日开盘溢价(%)": 0.0,
            "昨日创业板核心股次日盘中最高涨幅(%)": 0.0,
            "昨日创业板核心股次日收盘涨幅(%)": 0.0,
        }

        if previous_samples and not current_daily.empty:
            limit_stats = summarize_sample_feedback(current_daily, previous_samples.get("limit_up_codes", []))
            broken_stats = summarize_sample_feedback(current_daily, previous_samples.get("broken_codes", []))

            row["昨日创业板涨停样本数"] = limit_stats["sample_count"]
            row["昨日创业板涨停股次日开盘溢价(%)"] = limit_stats["avg_open"]
            row["昨日创业板涨停股次日收盘溢价(%)"] = limit_stats["avg_close"]
            row["昨日创业板炸板样本数"] = broken_stats["sample_count"]
            row["昨日创业板炸板股次日开盘溢价(%)"] = broken_stats["avg_open"]
            row["昨日创业板炸板股次日收盘溢价(%)"] = broken_stats["avg_close"]

            core_code = previous_samples.get("core_code")
            if core_code and core_code in current_daily.index:
                current_row = current_daily.loc[core_code]
                pre_close = pd.to_numeric(current_row["pre_close"], errors="coerce")
                if pd.notna(pre_close) and pre_close:
                    row["昨日创业板核心股"] = previous_samples.get("core_name") or core_code
                    row["昨日创业板核心股次日开盘溢价(%)"] = round((current_row["open"] / pre_close - 1) * 100, 2)
                    row["昨日创业板核心股次日盘中最高涨幅(%)"] = round((current_row["high"] / pre_close - 1) * 100, 2)
                    row["昨日创业板核心股次日收盘涨幅(%)"] = round((current_row["close"] / pre_close - 1) * 100, 2)

        rows.append(row)
        previous_date = trade_date

    return pd.DataFrame(rows, columns=CHINEXT_FEEDBACK_COLUMNS)


def normalize_daily_df(daily_df):
    if daily_df is None or daily_df.empty:
        return pd.DataFrame(columns=["ts_code", "open", "close", "high", "pre_close"]).set_index("ts_code")

    frame = daily_df.copy()
    for column in ["open", "close", "high", "pre_close"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.set_index("ts_code")


def summarize_sample_feedback(current_daily, ts_codes):
    matched = current_daily.loc[current_daily.index.intersection([str(code) for code in ts_codes])]
    if matched.empty:
        return {"sample_count": 0, "avg_open": 0.0, "avg_close": 0.0}

    pre_close = pd.to_numeric(matched["pre_close"], errors="coerce")
    valid = pre_close.notna() & (pre_close != 0)
    matched = matched[valid]
    pre_close = pre_close[valid]
    if matched.empty:
        return {"sample_count": 0, "avg_open": 0.0, "avg_close": 0.0}

    open_premium = (matched["open"] / pre_close - 1) * 100
    close_premium = (matched["close"] / pre_close - 1) * 100
    return {
        "sample_count": int(len(matched)),
        "avg_open": round(float(open_premium.mean()), 2),
        "avg_close": round(float(close_premium.mean()), 2),
    }
