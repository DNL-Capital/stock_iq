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


class stock_foreign:
    def __init__(self, symbol: str):
        """Truy vấn giao dịch khối ngoại cho một mã. / Foreign-trading accessor for a symbol."""
        self.symbol = symbol

    @wrap_errors()
    def foreign_history(
        self,
        interval: IntervalReport,
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Lịch sử giao dịch khối ngoại. / Foreign-trading history.

        Args:
            interval: days/months/quarters/years.
            start: ngày bắt đầu / start date.
            end: ngày kết thúc / end date.
        Returns:
            pd.DataFrame khối ngoại / foreign trading.
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
        cols_amount = [
            "foreignNetVolumeMatched",
            "foreignNetValueMatched",
            "foreignBuyVolumeMatched",
            "foreignBuyValueMatched",
            "foreignSellVolumeMatched",
            "foreignSellValueMatched",
            "foreignNetVolumeDeal",
            "foreignNetValueDeal",
            "foreignBuyVolumeDeal",
            "foreignBuyValueDeal",
            "foreignSellVolumeDeal",
            "foreignSellValueDeal",
            "foreignNetVolumeTotal",
            "foreignNetValueTotal",
            "foreignBuyVolumeTotal",
            "foreignBuyValueTotal",
            "foreignSellVolumeTotal",
            "foreignSellValueTotal",
        ]
        cols_percent = [
            "foreignRoomPercentage",  # (%)
            "foreignOwnedPercentage",  # (%)
            "foreignAvailablePercentage",
        ]  # (%)
        cols_data = (
            ["ticker", "tradingDate"]
            + cols_amount
            + cols_percent
            + ["foreignCurrentRoom"]
        )
        data = data[cols_data]
        data["tradingDate"] = pd.to_datetime(data["tradingDate"])
        data["tradingDate"] = reformat_period(data["tradingDate"], interval)
        data[cols_amount + ["foreignCurrentRoom"]] = data[
            cols_amount + ["foreignCurrentRoom"]
        ].astype(int)
        data[cols_percent] = data[cols_percent].apply(lambda x: round(x * 100, 2))
        rename_foreign = {
            "ticker": "symbol",
            "tradingDate": "date",
            "foreignNetVolumeMatched": "netMatchedVol",
            "foreignNetValueMatched": "netMatchedVal",
            "foreignBuyVolumeMatched": "buyMatchedVol",
            "foreignBuyValueMatched": "buyMatchedVal",
            "foreignSellVolumeMatched": "sellMatchedVol",
            "foreignSellValueMatched": "sellMatchedVal",
            "foreignNetVolumeDeal": "netDealVol",
            "foreignNetValueDeal": "netDealVal",
            "foreignBuyVolumeDeal": "buyDealVol",
            "foreignBuyValueDeal": "buyDealVal",
            "foreignSellVolumeDeal": "sellDealVol",
            "foreignSellValueDeal": "sellDealVal",
            "foreignNetVolumeTotal": "netTotalVol",
            "foreignNetValueTotal": "netTotalVal",
            "foreignBuyVolumeTotal": "buyTotalVol",
            "foreignBuyValueTotal": "buyTotalVal",
            "foreignSellVolumeTotal": "sellTotalVol",
            "foreignSellValueTotal": "sellTotalVal",
            "foreignRoomPercentage": "foreignRoomPct",
            "foreignOwnedPercentage": "foreignOwnedPct",
            "foreignAvailablePercentage": "foreignAvailablePct",
            "foreignCurrentRoom": "currentRoom",
        }
        data = data.rename(columns=rename_foreign)
        data = data.sort_values("date", ascending=True).reset_index(drop=True)
        return data

    @wrap_errors()
    def foreign_history_summary(self, interval: IntervalReport) -> pd.DataFrame:
        """Tổng hợp giao dịch khối ngoại. / Foreign-trading summary.

        Args:
            interval: days/months/quarters/years.
        Returns:
            pd.DataFrame tổng hợp khối ngoại / foreign summary.
        """
        headers = make_headers()
        validate_interval(interval, TIMEFRAME_REPORT)
        params = {"timeFrame": TIMEFRAME_REPORT[interval], "size": MAX_PAGE_SIZE}
        url_summary = (
            f"{IQ_URL}/company/{self.symbol.upper()}/price-history-summary"
        )
        response = NET.get(url_summary, headers=headers, params=params)
        data_summary = pd.json_normalize(response.json()["data"])
        cols_summary_foreign_total = [
            "foreignNetVolumeMatched",
            "foreignNetValueMatched",
            "foreignBuyVolumeMatched",
            "foreignBuyValueMatched",
            "foreignSellVolumeMatched",
            "foreignSellValueMatched",
            "foreignNetVolumeDeal",
            "foreignNetValueDeal",
            "foreignBuyVolumeDeal",
            "foreignBuyValueDeal",
            "foreignSellVolumeDeal",
            "foreignSellValueDeal",
            "foreignNetVolumeTotal",
            "foreignNetValueTotal",
            "foreignBuyVolumeTotal",
            "foreignBuyValueTotal",
            "foreignSellVolumeTotal",
            "foreignSellValueTotal",
        ]
        cols_summary_foreign_avg = [
            "foreignNetVolumeMatchedAvg",
            "foreignNetValueMatchedAvg",
            "foreignBuyVolumeMatchedAvg",
            "foreignBuyValueMatchedAvg",
            "foreignSellVolumeMatchedAvg",
            "foreignSellValueMatchedAvg",
            "foreignNetVolumeDealAvg",
            "foreignNetValueDealAvg",
            "foreignBuyVolumeDealAvg",
            "foreignBuyValueDealAvg",
            "foreignSellVolumeDealAvg",
            "foreignSellValueDealAvg",
            "foreignNetVolumeTotalAvg",
            "foreignNetValueTotalAvg",
            "foreignBuyVolumeTotalAvg",
            "foreignBuyValueTotalAvg",
            "foreignSellVolumeTotalAvg",
            "foreignSellValueTotalAvg",
        ]

        rename_summary = {
            "foreignNetVolumeMatched": "netMatchedVol",
            "foreignNetValueMatched": "netMatchedVal",
            "foreignBuyVolumeMatched": "buyMatchedVol",
            "foreignBuyValueMatched": "buyMatchedVal",
            "foreignSellVolumeMatched": "sellMatchedVol",
            "foreignSellValueMatched": "sellMatchedVal",
            "foreignNetVolumeDeal": "netDealVol",
            "foreignNetValueDeal": "netDealVal",
            "foreignBuyVolumeDeal": "buyDealVol",
            "foreignBuyValueDeal": "buyDealVal",
            "foreignSellVolumeDeal": "sellDealVol",
            "foreignSellValueDeal": "sellDealVal",
            "foreignNetVolumeTotal": "netTotalVol",
            "foreignNetValueTotal": "netTotalVal",
            "foreignBuyVolumeTotal": "buyTotalVol",
            "foreignBuyValueTotal": "buyTotalVal",
            "foreignSellVolumeTotal": "sellTotalVol",
            "foreignSellValueTotal": "sellTotalVal",
            "foreignNetVolumeMatchedAvg": "netMatchedVolAvg",
            "foreignNetValueMatchedAvg": "netMatchedValAvg",
            "foreignBuyVolumeMatchedAvg": "buyMatchedVolAvg",
            "foreignBuyValueMatchedAvg": "buyMatchedValAvg",
            "foreignSellVolumeMatchedAvg": "sellMatchedVolAvg",
            "foreignSellValueMatchedAvg": "sellMatchedValAvg",
            "foreignNetVolumeDealAvg": "netDealVolAvg",
            "foreignNetValueDealAvg": "netDealValAvg",
            "foreignBuyVolumeDealAvg": "buyDealVolAvg",
            "foreignBuyValueDealAvg": "buyDealValAvg",
            "foreignSellVolumeDealAvg": "sellDealVolAvg",
            "foreignSellValueDealAvg": "sellDealValAvg",
            "foreignNetVolumeTotalAvg": "totalNetVolAvg",
            "foreignNetValueTotalAvg": "totalNetValAvg",
            "foreignBuyVolumeTotalAvg": "totalBuyVolAvg",
            "foreignBuyValueTotalAvg": "totalBuyValAvg",
            "foreignSellVolumeTotalAvg": "totalSellVolAvg",
            "foreignSellValueTotalAvg": "totalSellValAvg",
        }
        data_summary_his_total = data_summary[cols_summary_foreign_total]
        data_summary_his_total.insert(0, "symbol", self.symbol.upper())
        data_summary_his_total.insert(1, "type", "total")
        data_summary_his_total = data_summary_his_total.rename(
            columns=rename_summary
        )
        data_summary_his_avg = data_summary[cols_summary_foreign_avg]
        data_summary_his_avg.insert(0, "symbol", self.symbol.upper())
        data_summary_his_avg.insert(1, "type", "average")
        data_summary_his_avg = data_summary_his_avg.rename(columns=rename_summary)
        data_summary = pd.concat(
            [data_summary_his_total, data_summary_his_avg], axis=0
        )
        cols = data_summary.columns[2:]
        data_summary[cols] = data_summary[cols].round(0).astype("Int64")
        return data_summary
