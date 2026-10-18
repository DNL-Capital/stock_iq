import pandas as pd
from pandas import json_normalize

from ...core._http import NET
from ...core.constants import IQ_URL, MAX_PAGE_SIZE, make_headers
from ...core.exceptions import DataFetchError, wrap_errors
from ...core.utils import to_day, to_yyyymmdd


class indice:
    # Vietcap phân biệt hoa/thường; ánh xạ các cách viết thường gặp về mã chuẩn.
    _CODES = {
        "HNXINDEX": "HNXIndex",
        "HNX": "HNXIndex",
        "UPCOM": "HNXUpcomIndex",
        "UPINDEX": "HNXUpcomIndex",
        "UPCOMINDEX": "HNXUpcomIndex",
        "HNXUPCOMINDEX": "HNXUpcomIndex",
    }

    def __init__(self, indice: str):
        """Truy vấn dữ liệu chỉ số. / Index accessor."""
        self.indice = self._CODES.get(indice.upper(), indice.upper())

    @wrap_errors()
    def market(self, start: str, end: str) -> pd.DataFrame:
        """Tổng quan chỉ số theo khoảng ngày. / Index overview over a date range.

        Args:
            start: ngày bắt đầu / start date.
            end: ngày kết thúc / end date.
        Returns:
            pd.DataFrame tổng quan chỉ số / index overview.
        """
        params = {
            "timeFrame": "ONE_DAY",
            "fromDate": to_yyyymmdd(start, "start"),
            "toDate": to_yyyymmdd(end, "end"),
            "size": MAX_PAGE_SIZE,
            "index": self.indice,
        }
        url = f"{IQ_URL}/market-indices/history"
        response = NET.get(url, headers=make_headers(), params=params)
        data = json_normalize(response.json()["data"]["content"])
        if data.empty:
            raise DataFetchError(f"Không có dữ liệu cho chỉ số '{self.indice}'")

        data = data[
            [
                "tradingDate",
                "symbol",
                "closeIndex",
                "totalVolume",
                "totalValue",
                "foreignBuyVolumeTotal",
                "foreignSellVolumeTotal",
                "foreignBuyValueTotal",
                "foreignSellValueTotal",
            ]
        ].rename(
            columns={
                "tradingDate": "date",
                "symbol": "exchange",
                "closeIndex": "closePrice",
                "totalVolume": "totalVol",
                "totalValue": "totalVal",
                "foreignBuyVolumeTotal": "buyForeignQuantity",
                "foreignSellVolumeTotal": "sellForeignQuantity",
                "foreignBuyValueTotal": "buyForeignVal",
                "foreignSellValueTotal": "sellForeignVal",
            }
        )
        cols = [
            "totalVol",
            "totalVal",
            "buyForeignQuantity",
            "sellForeignQuantity",
            "buyForeignVal",
            "sellForeignVal",
        ]
        data[cols] = (
            data[cols].apply(pd.to_numeric, errors="coerce").round().astype("Int64")
        )
        data["date"] = to_day(data["date"])
        data["netForeignVal"] = data["buyForeignVal"] - data["sellForeignVal"]
        return data.sort_values("date", ascending=True).reset_index(drop=True)
