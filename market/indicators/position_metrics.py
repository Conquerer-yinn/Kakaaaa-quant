import pandas as pd


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


