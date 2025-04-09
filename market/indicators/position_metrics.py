import pandas as pd


def build_position_frame(series):
    # 这里用 expanding 窗口，表达“当前值在已有观察区间里的位置”。
    numeric = pd.to_numeric(series, errors="coerce")
    frame = pd.DataFrame({"value": numeric})
    frame["近期低点"] = numeric.expanding().min()
    frame["近期高点"] = numeric.expanding().max()
    frame["中枢"] = numeric.expanding().median()

    return frame[["近期低点", "近期高点", "中枢"]]


