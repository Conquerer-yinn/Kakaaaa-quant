"""连板样本研究：跟踪连板梯队的隔日表现。

样本池：当日连板数达到门槛的涨停股（按代码去重）。
隔日表现：次日开盘 / 收盘相对样本日收盘的溢价；次日停牌样本剔除。
环境过滤：读取情绪历史主表，情绪冰点时提示暂停跟踪。
核心逻辑保持纯函数，方便离线测试。
"""
from __future__ import annotations

import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from strategies.utils import coerce_numeric, filter_limit_up

SAMPLE_COLUMNS = ["日期", "ts_code", "名称", "连板数"]
FEEDBACK_COLUMNS = SAMPLE_COLUMNS + ["次日开盘溢价(%)", "次日收盘溢价(%)"]


def build_follow_samples(trade_date, limit_df, min_streak: int = 2) -> pd.DataFrame:
    """从涨停名单里取出连板数达到门槛的样本，按代码去重。"""
    limit_up = filter_limit_up(limit_df)
    if limit_up.empty:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)

    samples = limit_up[limit_up["limit_times"] >= min_streak]
    if samples.empty:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)

    result = pd.DataFrame(
        {
            "日期": str(trade_date),
            "ts_code": samples["ts_code"].astype(str),
            "名称": samples.get("name"),
            "连板数": samples["limit_times"].astype(int),
        }
    )[SAMPLE_COLUMNS].sort_values("连板数", ascending=False)
    # 同一代码在名单里出现多次时，只保留连板数最高的一条。
    result = result.drop_duplicates(subset=["ts_code"], keep="first")
    return result.reset_index(drop=True)


def evaluate_next_day(samples_df, next_daily_df) -> pd.DataFrame:
    """给样本补上次日开盘 / 收盘溢价；次日无行情（停牌）样本直接剔除。"""
    if samples_df is None or samples_df.empty:
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)
    if next_daily_df is None or next_daily_df.empty:
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)

    daily = coerce_numeric(next_daily_df, ["open", "close", "pre_close"])

    merged = samples_df.merge(
        daily[["ts_code", "open", "close", "pre_close"]],
        on="ts_code",
        how="left",
    )
    valid = (
        merged["pre_close"].notna()
        & (merged["pre_close"] != 0)
        & merged["open"].notna()
        & merged["close"].notna()
    )
    merged = merged[valid].copy()
    if merged.empty:
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)

    merged["次日开盘溢价(%)"] = ((merged["open"] / merged["pre_close"] - 1) * 100).round(2)
    merged["次日收盘溢价(%)"] = ((merged["close"] / merged["pre_close"] - 1) * 100).round(2)
    return merged[FEEDBACK_COLUMNS].reset_index(drop=True)


def summarize_feedback(feedback_df) -> dict:
    """汇总样本平均表现，供复盘和摘要卡片使用。"""
    if feedback_df is None or feedback_df.empty:
        return {"sample_count": 0, "avg_open_premium": None, "avg_close_premium": None}

    open_premium = pd.to_numeric(feedback_df["次日开盘溢价(%)"], errors="coerce").dropna()
    close_premium = pd.to_numeric(feedback_df["次日收盘溢价(%)"], errors="coerce").dropna()
    return {
        "sample_count": int(len(feedback_df)),
        "avg_open_premium": round(float(open_premium.mean()), 2) if not open_premium.empty else None,
        "avg_close_premium": round(float(close_premium.mean()), 2) if not close_premium.empty else None,
    }


def load_sentiment_env() -> dict | None:
    """读取最新情绪历史主表，取最近一行总市场数据作为环境参考。

    读取失败时返回 None，不阻塞策略本身。
    """
    try:
        from market.services.market_sentiment_workbook import find_latest_history_workbook
        from storage.excel_helper import ExcelHelper

        latest = find_latest_history_workbook()
        if latest is None:
            return None
        df = ExcelHelper.read_sheet(latest.file_name, "总市场数据")
        if df is None or df.empty:
            return None
        row = df.iloc[-1]
        return {
            "日期": row.get("日期"),
            "涨停数": row.get("涨停数"),
            "炸板数": row.get("炸板数"),
            "最高连板": row.get("最高连板"),
        }
    except Exception:
        return None


def should_follow_by_env(env: dict | None, min_limit_up: int = 30) -> bool:
    """情绪冰点（涨停家数过少）时提示暂停连板跟踪。环境缺失时默认继续。"""
    if not env:
        return True
    limit_up = pd.to_numeric(pd.Series([env.get("涨停数")]), errors="coerce").iloc[0]
    if pd.isna(limit_up):
        return True
    return int(limit_up) >= min_limit_up


def run(trade_date: str):
    """抓取指定交易日的涨停名单，登记连板样本池。"""
    from data_engine.tushare_api import TushareDataEngine
    from strategies.strategy_output import write_strategy_result

    env = load_sentiment_env()
    if not should_follow_by_env(env):
        print(f"{trade_date} 情绪环境偏冷（涨停数过少），本次跳过连板跟踪。")
        return None

    engine = TushareDataEngine()
    limit_df = engine.get_limit_list(trade_date)
    samples = build_follow_samples(trade_date, limit_df)
    if samples.empty:
        print(f"{trade_date} 没有满足条件的连板样本。")
        return None

    output_path = write_strategy_result(samples, "limit_up_follow")
    print(f"Wrote {len(samples)} rows to {output_path}")
    return output_path


if __name__ == "__main__":
    from datetime import datetime

    run(datetime.today().strftime("%Y%m%d"))
