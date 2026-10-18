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


class stock_price:
    def __init__(self, symbol: str):
        """Truy vấn lịch sử giá chi tiết cho một mã. / Price-history accessor for a symbol."""
        self.symbol = symbol

    @wrap_errors()
    def price_history(
        self,
        interval: IntervalReport,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Lịch sử giá chi tiết theo kỳ. / Detailed price history by period.

        Args:
            interval: days/months/quarters/years.
            start: ngày bắt đầu / start date.
            end: ngày kết thúc / end date.
        Returns:
            pd.DataFrame giá / price history.
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
        cols_price = [
            "closePriceAdjusted",
            "openPriceAdjusted",
            "highestPriceAdjusted",
            "lowestPriceAdjusted",
        ]
        col_volume = [
            "totalMatchVolume",
            "totalMatchValue",
            "totalDealVolume",
            "totalDealValue",
            "totalVolume",
            "totalValue",
            "totalBuyUnmatchedVolume",
            "totalSellUnmatchedVolume",
            "marketCap",
        ]
        cols_pricehis = (
            ["ticker", "tradingDate", "priceChange", "percentPriceChangeAdjusted"]
            + cols_price
            + col_volume
        )
        data = data[cols_pricehis]
        data["tradingDate"] = pd.to_datetime(data["tradingDate"])
        data["tradingDate"] = reformat_period(data["tradingDate"], interval)
        price_cols = ["priceChange"] + cols_price
        data[price_cols] = (data[price_cols] / 1000).round(2)
        data["percentPriceChangeAdjusted"] = data[
            "percentPriceChangeAdjusted"
        ].apply(lambda x: round(x * 100, 2))
        data[col_volume] = data[col_volume].fillna(0).round(0).astype(int)
        rename_his = {
            "ticker": "symbol",
            "tradingDate": "date",
            "percentPriceChangeAdjusted": "ratioChange",
            "closePriceAdjusted": "close",
            "openPriceAdjusted": "open",
            "highestPriceAdjusted": "high",
            "lowestPriceAdjusted": "low",
            "totalMatchVolume": "totalMatchVol",
            "totalMatchValue": "totalMatchVal",
            "totalDealVolume": "totalDealVol",
            "totalDealValue": "totalDealVal",
            "totalVolume": "totalVol",
            "totalValue": "totalVal",
            "totalBuyUnmatchedVolume": "totalBuyUnmatchedVol",
            "totalSellUnmatchedVolume": "totalSellUnmatchedVol",
        }
        data = data.rename(columns=rename_his)
        data = data.sort_values("date", ascending=True).reset_index(drop=True)
        return data

    @wrap_errors()
    def price_history_summary(self, interval: IntervalReport) -> pd.DataFrame:
        """Tổng hợp giá theo kỳ. / Price summary by period.

        Args:
            interval: days/months/quarters/years.
        Returns:
            pd.DataFrame tổng hợp giá / price summary.
        """
        headers = make_headers()
        validate_interval(interval, TIMEFRAME_REPORT)
        params = {"timeFrame": TIMEFRAME_REPORT[interval], "size": MAX_PAGE_SIZE}

        url_summary = (
            f"{IQ_URL}/company/{self.symbol.upper()}/price-history-summary"
        )
        response = NET.get(url_summary, headers=headers, params=params)
        data_summary = pd.json_normalize(response.json()["data"])
        cols_summary_his_total = [
            "totalMatchVolume",
            "totalMatchValue",
            "totalDealVolume",
            "totalDealValue",
            "totalVolume",
            "totalValue",
            "totalBuyUnmatchedVolume",
            "totalSellUnmatchedVolume",
        ]
        cols_summary_his_avg = [
            "averageMatchVolume",
            "averageMatchValue",
            "averageDealVolume",
            "averageDealValue",
            "averageVolume",
            "averageValue",
            "totalBuyUnmatchedVolumeAvg",
            "totalSellUnmatchedVolumeAvg",
        ]

        rename_summary = {
            "totalMatchVolume": "totalMatchVol",
            "totalMatchValue": "totalMatchVal",
            "totalDealVolume": "totalDealVol",
            "totalDealValue": "totalDealVal",
            "totalVolume": "totalVol",
            "totalValue": "totalVal",
            "totalBuyUnmatchedVolume": "totalBuyUnmatchedVol",
            "totalSellUnmatchedVolume": "totalSellUnmatchedVol",
            "averageMatchVolume": "avgMatchVol",
            "averageMatchValue": "avgMatchVal",
            "averageDealVolume": "avgDealVol",
            "averageDealValue": "avgDealVal",
            "averageVolume": "avgVol",
            "averageValue": "avgVal",
            "totalBuyUnmatchedVolumeAvg": "avgTotalBuyUnmatchedVol",
            "totalSellUnmatchedVolumeAvg": "avgTotalSellUnmatchedVol",
        }

        data_summary_his_total = data_summary[cols_summary_his_total]
        data_summary_his_total.insert(0, "symbol", self.symbol.upper())
        data_summary_his_total.insert(1, "type", "total")
        data_summary_his_total = data_summary_his_total.rename(
            columns=rename_summary
        )

        data_summary_his_avg = data_summary[cols_summary_his_avg]
        data_summary_his_avg.insert(0, "symbol", self.symbol.upper())
        data_summary_his_avg.insert(1, "type", "average")
        data_summary_his_avg = data_summary_his_avg.rename(columns=rename_summary)

        data_summary = pd.concat(
            [data_summary_his_total, data_summary_his_avg], axis=0
        )
        cols = data_summary.columns[2:]
        data_summary[cols] = data_summary[cols].round(0).astype("Int64")
        return data_summary
