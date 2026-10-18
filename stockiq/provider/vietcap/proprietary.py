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


class stock_proprietary:
    def __init__(self, symbol: str):
        """Truy vấn giao dịch tự doanh cho một mã. / Proprietary-trading accessor for a symbol."""
        self.symbol = symbol

    @wrap_errors()
    def proprietary_history(
        self,
        interval: IntervalReport,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Lịch sử giao dịch tự doanh. / Proprietary-trading history.

        Args:
            interval: days/months/quarters/years.
            start: ngày bắt đầu / start date.
            end: ngày kết thúc / end date.
        Returns:
            pd.DataFrame tự doanh / proprietary trading.
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
        url = f"{IQ_URL}/company/{self.symbol.upper()}/proprietary-history"
        response = NET.get(url, headers=headers, params=params)
        data = json_normalize(response.json()["data"]["content"])
        cols_volval = [
            "totalMatchTradeNetVolume",
            "totalMatchTradeNetValue",
            "totalMatchBuyTradeVolume",
            "totalMatchBuyTradeValue",
            "totalMatchSellTradeVolume",
            "totalMatchSellTradeValue",
            "totalDealTradeNetVolume",
            "totalDealTradeNetValue",
            "totalDealBuyTradeVolume",
            "totalDealBuyTradeValue",
            "totalDealSellTradeVolume",
            "totalDealSellTradeValue",
            "totalTradeNetVolume",
            "totalTradeNetValue",
            "totalBuyTradeVolume",
            "percentBuyTradeVolume",
            "totalBuyTradeValue",
            "percentBuyTradeValue",
            "totalSellTradeVolume",
            "percentSellTradeVolume",
            "totalSellTradeValue",
            "percentSellTradeValue",
        ]
        cols_percent = [
            "percentBuyTradeVolume",
            "percentBuyTradeValue",
            "percentSellTradeVolume",
            "percentSellTradeValue",
        ]
        int_cols = list(set(cols_volval) - set(cols_percent))
        cols_prop = ["ticker", "tradingDate"] + cols_volval
        data = data[cols_prop]
        data["tradingDate"] = pd.to_datetime(data["tradingDate"])
        data["tradingDate"] = reformat_period(data["tradingDate"], interval)
        data[cols_percent] = data[cols_percent].apply(lambda x: round(x * 100, 2))
        data[int_cols] = data[int_cols].fillna(0).round(0).astype(int)
        rename_prop = {
            "ticker": "symbol",
            "tradingDate": "date",
            "totalMatchTradeNetVolume": "netMatchedVol",
            "totalMatchTradeNetValue": "netMatchedVal",
            "totalMatchBuyTradeVolume": "buyMatchedVol",
            "totalMatchBuyTradeValue": "buyMatchedVal",
            "totalMatchSellTradeVolume": "sellMatchedVol",
            "totalMatchSellTradeValue": "sellMatchedVal",
            "totalDealTradeNetVolume": "netNegotiatedVol",
            "totalDealTradeNetValue": "netNegotiatedVal",
            "totalDealBuyTradeVolume": "buyNegotiatedVol",
            "totalDealBuyTradeValue": "buyNegotiatedVal",
            "totalDealSellTradeVolume": "sellNegotiatedVol",
            "totalDealSellTradeValue": "sellNegotiatedVal",
            "totalTradeNetVolume": "netTotalVol",
            "totalTradeNetValue": "netTotalVal",
            "totalBuyTradeVolume": "buyTotalVol",
            "percentBuyTradeVolume": "buyVolPct",
            "totalBuyTradeValue": "buyTotalVal",
            "percentBuyTradeValue": "buyValPct",
            "totalSellTradeVolume": "sellTotalVol",
            "percentSellTradeVolume": "sellVolPct",
            "totalSellTradeValue": "sellTotalVal",
            "percentSellTradeValue": "sellValPct",
        }
        data = data.rename(columns=rename_prop)
        data = data.sort_values("date", ascending=True).reset_index(drop=True)
        return data

    @wrap_errors()
    def proprietary_history_summary(self, interval: IntervalReport) -> pd.DataFrame:
        """Tổng hợp giao dịch tự doanh. / Proprietary-trading summary.

        Args:
            interval: days/months/quarters/years.
        Returns:
            pd.DataFrame tổng hợp tự doanh / proprietary summary.
        """
        headers = make_headers()
        validate_interval(interval, TIMEFRAME_REPORT)
        params = {"timeFrame": TIMEFRAME_REPORT[interval], "size": MAX_PAGE_SIZE}
        url_sumary = (
            f"{IQ_URL}/company/{self.symbol.upper()}/proprietary-history-summary"
        )
        response = NET.get(url_sumary, headers=headers, params=params)
        data_sumary = pd.json_normalize(response.json()["data"])
        cols_sumary_prop_total = [
            "totalMatchTradeNetVolume",
            "totalMatchTradeNetValue",
            "totalMatchBuyTradeVolume",
            "totalMatchBuyTradeValue",
            "totalMatchSellTradeVolume",
            "totalMatchSellTradeValue",
            "totalDealTradeNetVolume",
            "totalDealTradeNetValue",
            "totalDealBuyTradeVolume",
            "totalDealBuyTradeValue",
            "totalDealSellTradeVolume",
            "totalDealSellTradeValue",
            "totalTradeNetVolume",
            "totalTradeNetValue",
            "totalBuyTradeVolume",
            "percentBuyTradeVolume",
            "totalBuyTradeValue",
            "percentBuyTradeValue",
            "totalSellTradeVolume",
            "percentSellTradeVolume",
            "totalSellTradeValue",
            "percentSellTradeValue",
        ]

        cols_sumary_prop_avg = [
            "averageTotalMatchNetVolume",
            "averageTotalMatchNetValue",
            "averageTotalMatchBuyTradeVolume",
            "averageTotalMatchBuyTradeValue",
            "averageTotalMatchSellTradeVolume",
            "averageTotalMatchSellTradeValue",
            "averageTotalDealNetVolume",
            "averageTotalDealNetValue",
            "averageTotalDealBuyTradeVolume",
            "averageTotalDealBuyTradeValue",
            "averageTotalDealSellTradeVolume",
            "averageTotalDealSellTradeValue",
            "averageTotalTradeNetVolume",
            "averageTotalTradeNetValue",
            "averageTotalBuyTradeVolume",
            "averagePercentBuyTradeVolume",
            "averageTotalBuyTradeValue",
            "averagePercentBuyTradeValue",
            "averageTotalSellTradeVolume",
            "averagePercentSellTradeVolume",
            "averageTotalSellTradeValue",
            "averagePercentSellTradeValue",
        ]
        rename_summary = {
            # Khớp lệnh
            "totalMatchTradeNetVolume": "netMatchedVol",
            "totalMatchTradeNetValue": "netMatchedVal",
            "totalMatchBuyTradeVolume": "buyMatchedVol",
            "totalMatchBuyTradeValue": "buyMatchedVal",
            "totalMatchSellTradeVolume": "sellMatchedVol",
            "totalMatchSellTradeValue": "sellMatchedVal",
            "averageTotalMatchNetVolume": "netMatchedVol",
            "averageTotalMatchNetValue": "netMatchedVal",
            "averageTotalMatchBuyTradeVolume": "buyMatchedVol",
            "averageTotalMatchBuyTradeValue": "buyMatchedVal",
            "averageTotalMatchSellTradeVolume": "sellMatchedVol",
            "averageTotalMatchSellTradeValue": "sellMatchedVal",
            # Thỏa thuận
            "totalDealTradeNetVolume": "netDealVol",
            "totalDealTradeNetValue": "netDealVal",
            "totalDealBuyTradeVolume": "buyDealVol",
            "totalDealBuyTradeValue": "buyDealVal",
            "totalDealSellTradeVolume": "sellDealVol",
            "totalDealSellTradeValue": "sellDealVal",
            "averageTotalDealNetVolume": "netDealVol",
            "averageTotalDealNetValue": "netDealVal",
            "averageTotalDealBuyTradeVolume": "buyDealVol",
            "averageTotalDealBuyTradeValue": "buyDealVal",
            "averageTotalDealSellTradeVolume": "sellDealVol",
            "averageTotalDealSellTradeValue": "sellDealVal",
            # Tổng mua bán ròng
            "totalTradeNetVolume": "netTotalVol",
            "totalTradeNetValue": "netTotalVal",
            "totalBuyTradeVolume": "buyTotalVol",
            "percentBuyTradeVolume": "buyVolPct",
            "totalBuyTradeValue": "buyTotalVal",
            "percentBuyTradeValue": "buyValPct",
            "totalSellTradeVolume": "sellTotalVol",
            "percentSellTradeVolume": "sellVolPct",
            "totalSellTradeValue": "sellTotalVal",
            "percentSellTradeValue": "sellValPct",
            "averageTotalTradeNetVolume": "netAvgTotalVol",
            "averageTotalTradeNetValue": "netAvgTotalVal",
            "averageTotalBuyTradeVolume": "buyAvgTotalVol",
            "averagePercentBuyTradeVolume": "avgBuyVolPct",
            "averageTotalBuyTradeValue": "buyAvgTotalVal",
            "averagePercentBuyTradeValue": "avgBuyValPct",
            "averageTotalSellTradeVolume": "sellAvgTotalVol",
            "averagePercentSellTradeVolume": "avgSellVolPct",
            "averageTotalSellTradeValue": "sellAvgTotalVal",
            "averagePercentSellTradeValue": "avgSellValPct",
        }
        data_sumary_prop_total = data_sumary[cols_sumary_prop_total]
        data_sumary_prop_total.insert(0, "symbol", self.symbol.upper())
        data_sumary_prop_total.insert(1, "type", "total")
        data_sumary_prop_total = data_sumary_prop_total.rename(
            columns=rename_summary
        )
        data_sumary_prop_avg = data_sumary[cols_sumary_prop_avg]
        data_sumary_prop_avg.insert(0, "symbol", self.symbol.upper())
        data_sumary_prop_avg.insert(1, "type", "average")
        data_sumary_prop_avg = data_sumary_prop_avg.rename(columns=rename_summary)
        data_sumary = pd.concat(
            [data_sumary_prop_total, data_sumary_prop_avg], axis=0
        )
        cols_percent = [
            "buyVolPct",
            "buyValPct",
            "sellVolPct",
            "sellValPct",
            "avgBuyVolPct",
            "avgBuyValPct",
            "avgSellVolPct",
            "avgSellValPct",
        ]
        int_cols = list(set(data_sumary.columns[2:]) - set(cols_percent))
        data_sumary[cols_percent] = data_sumary[cols_percent].mul(100).round(2)
        data_sumary[int_cols] = data_sumary[int_cols].round(0).astype("Int64")
        return data_sumary
