import pandas as pd


def append_position_columns(df, metric_columns):
    # 位置度量只做辅助判断，不改变原始指标本身。
    result = df.copy()
    for column in metric_columns:
        if column not in result.columns:
            continue
        position_df = build_position_frame(result[column])
        result[f"{column}位置"] = position_df["位置"]
        result[f"{column}相对中枢"] = position_df["相对中枢"]
    return result


def build_position_frame(series):
    # 这里用 expanding 窗口，表达“当前值在已有观察区间里的位置”。
    numeric = pd.to_numeric(series, errors="coerce")
    frame = pd.DataFrame({"value": numeric})
    frame["近期低点"] = numeric.expanding().min()
    frame["近期高点"] = numeric.expanding().max()
    frame["中枢"] = numeric.expanding().median()

    def classify(row):
        value = row["value"]
        low = row["近期低点"]
        high = row["近期高点"]
        middle = row["中枢"]

        if pd.isna(value):
            return pd.Series({"位置": None, "相对中枢": None})

        if pd.isna(low) or pd.isna(high) or high == low:
            return pd.Series({"位置": "中位", "相对中枢": "接近中枢"})

        ratio = (value - low) / (high - low)
        if ratio >= 0.67:
            position = "偏高"
        elif ratio <= 0.33:
            position = "偏低"
        else:
            position = "中位"

        band = (high - low) * 0.1
        if value >= middle + band:
            relative = "强于中枢"
        elif value <= middle - band:
            relative = "弱于中枢"
        else:
            relative = "接近中枢"

        return pd.Series({"位置": position, "相对中枢": relative})

    frame[["位置", "相对中枢"]] = frame.apply(classify, axis=1)
    return frame[["近期低点", "近期高点", "位置", "相对中枢"]]


