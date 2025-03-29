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


