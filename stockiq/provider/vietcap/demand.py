import pandas as pd
from pandas import json_normalize

from ...core._http import NET
from ...core.constants import (
    IQ_URL,
    MAX_PAGE_SIZE,
    TIMEFRAME_REPORT,
    make_headers,
)
from ...core.exceptions import validate_interval, wrap_errors
from ...core.types import IntervalReport
from ...core.utils import range_to_yyyymmdd, reformat_period


class stock_demand:
    def __init__(self, symbol: str):
        """Truy vấn cung–cầu cho một mã. / Supply–demand accessor for a symbol."""
        self.symbol = symbol

    @wrap_errors()
    def demand_history(
        self, interval: IntervalReport, start: str, end: str
    ) -> pd.DataFrame:
        """Lịch sử cung–cầu (dư mua/bán). / Supply–demand history.

        Args:
            interval: days/months/quarters/years.
            start: ngày bắt đầu / start date.
            end: ngày kết thúc / end date.
        Returns:
            pd.DataFrame cung–cầu / supply–demand.
        """
        headers = make_headers()
        validate_interval(interval, TIMEFRAME_REPORT)
        start_date, end_date = range_to_yyyymmdd(interval, start, end)
        params = {
            "timeFrame": TIMEFRAME_REPORT[interval],
            "fromDate": start_date,
            "toDate": end_date,
            "size": MAX_PAGE_SIZE,
        }
        url = f"{IQ_URL}/company/{self.symbol.upper()}/price-history"
        response = NET.get(url, headers=headers, params=params)
        data = json_normalize(response.json()["data"]["content"])
        cols_demand = [
            "ticker",
            "tradingDate",
            "totalBuyUnmatchedVolume",
            "totalSellUnmatchedVolume",
            "totalBuyTrade",
            "totalSellTrade",
            "totalBuyTradeVolume",
            "totalSellTradeVolume",
            "averageBuyTradeVolume",
            "averageSellTradeVolume",
            "totalNetTradeVolume",
        ]
        data = data[cols_demand]
        data["tradingDate"] = pd.to_datetime(data["tradingDate"])
        data["tradingDate"] = reformat_period(data["tradingDate"], interval)
        rename_his = {
            "ticker": "symbol",
            "tradingDate": "date",
            "totalBuyUnmatchedVolume": "totalBuyUnmatchedVol",
            "totalSellUnmatchedVolume": "totalSellUnmatchedVol",
            "totalBuyTradeVolume": "totalBuyVol",
            "totalSellTradeVolume": "totalSellVol",
            "averageBuyTradeVolume": "avgBuyTradeVol",
            "averageSellTradeVolume": "avgSellTradeVol",
            "totalNetTradeVolume": "totalNetTradeVol",
        }
        data = data.rename(columns=rename_his)
        cols = data.columns[2:]
        data[cols] = data[cols].round(0).astype("Int64")
        data = data.sort_values("date", ascending=True).reset_index(drop=True)
        return data
