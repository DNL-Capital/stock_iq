import json
import re
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from pandas import json_normalize

from ...core._http import NET
from ...core.constants import (
    BIG_ORDER_LIMIT,
    IQ_URL,
    MAX_PAGE_SIZE,
    OHLC_COUNT_BACK,
    REFERER_VIETCAP_FLAT,
    REFERER_VIETCAP_STOCK,
    TIMEFRAME_OHLC,
    TRADING_URL,
    make_headers,
)
from ...core.exceptions import validate_interval, wrap_errors
from ...core.types import ExchangeStr, IntervalOHLC
from ...core.utils import parse_date

# Mã niêm yết giá theo VND: cổ phiếu, ETF/quỹ đóng, chứng quyền, trái phiếu.
# Phái sinh (điểm) và chỉ số không khớp nên giữ nguyên giá.
# VND-priced codes: stocks, ETFs/closed-end funds, covered warrants, bonds.
_VND_PRICED = re.compile(
    r"[A-Z0-9]{3}|E1VFVN30|FU[A-Z0-9]{6}|C[A-Z0-9]{3}\d{4}|[A-Z]{3,4}\d{5,6}"
)


def _price_scale(symbol: str) -> int:
    """Hệ số đổi giá về nghìn VND. / Divisor turning prices into thousand VND."""
    return 1000 if _VND_PRICED.fullmatch(symbol.upper()) else 1


def _is_derivative(symbol: str) -> bool:
    """Mã phái sinh kiểu cũ (VN30F1M, GB05F2612) hoặc KRX (41I1GA000)."""
    return bool(re.fullmatch(r"(VN30|VN100|GB05|GB10)F\w+|4[12]\w{7}", symbol.upper()))


class stock_market:
    def __init__(self, symbol: str):
        """Truy vấn dữ liệu thị trường cho một mã. / Market-data accessor for a symbol."""
        self.symbol = symbol

    @wrap_errors()
    def stock_info(self, exchange: Optional[ExchangeStr] = None) -> pd.DataFrame:
        """Thông tin niêm yết của mã. / Listing info (exchange, name, sector).

        Args:
            exchange: lọc theo sàn HOSE/HNX/UPCOM / optional exchange filter.
        Returns:
            pd.DataFrame thông tin mã / symbol info.
        """
        headers = make_headers()
        payload = {"pageSize": MAX_PAGE_SIZE}
        url = f"{IQ_URL}/screening/paging"
        response = NET.post(url, headers=headers, data=json.dumps(payload))
        data = pd.json_normalize(response.json()["data"]["content"])
        cols = [
            "ticker",
            "exchange",
            "viSector",
            "viOrganName",
            "enSector",
            "enOrganName",
        ]
        data = data[cols]
        rename_cols = {"ticker": "symbol"}
        data = data.rename(columns=rename_cols)
        data["symbol"] = data["symbol"].astype(str).str.upper()

        if exchange is None:
            return data.loc[data["symbol"] == self.symbol.upper()].reset_index(
                drop=True
            )

        return data.loc[
            (data["symbol"] == self.symbol.upper())
            & (data["exchange"] == exchange.upper())
        ].reset_index(drop=True)

    @wrap_errors()
    def history(self, interval: IntervalOHLC, start: str, end: str) -> pd.DataFrame:
        """Lịch sử giá OHLC theo khung thời gian. / OHLC price history by timeframe.

        Args:
            interval: days/months/minutes/hours.
            start: ngày bắt đầu "YYYY-MM-DD" / start date.
            end: ngày kết thúc "YYYY-MM-DD" / end date.
        Returns:
            pd.DataFrame giá lịch sử / price history (rỗng nếu không có dữ liệu).
        """
        headers = make_headers(REFERER_VIETCAP_STOCK)

        start_dt = parse_date(start, "start")
        end_dt = parse_date(end, "end") + timedelta(days=1)
        end_timestamp = end_dt.timestamp()
        validate_interval(interval, TIMEFRAME_OHLC)

        payload = {
            "timeFrame": TIMEFRAME_OHLC[interval],
            "symbols": [self.symbol.upper()],
            "countBack": OHLC_COUNT_BACK,
            "to": end_timestamp,
        }

        url = f"{TRADING_URL}/chart/OHLCChart/gap-chart"

        response = NET.post(url, headers=headers, data=json.dumps(payload))
        json_data = response.json()

        if not json_data or not isinstance(json_data, list) or len(json_data) == 0:
            return pd.DataFrame()

        data = json_data[0]

        df = pd.DataFrame(data)
        df = df[["symbol", "t", "o", "c", "h", "l", "v"]]
        df["t"] = pd.to_numeric(df["t"], errors="coerce")
        df["t"] = df["t"].apply(lambda x: datetime.fromtimestamp(x))
        if interval in ["minutes", "hours"]:
            df["t"] = (
                pd.to_datetime(df["t"], errors="coerce")
                .dt.tz_localize(None)
                .dt.floor("s")
            )
        if interval in ["days", "months"]:
            df["t"] = (
                pd.to_datetime(df["t"], errors="coerce")
                .dt.tz_localize(None)
                .dt.floor("d")
            )
        df = df.sort_values(by="t", ascending=True).reset_index(drop=True)

        scale = _price_scale(self.symbol)
        if scale != 1:
            df[["o", "h", "l", "c"]] = df[["o", "h", "l", "c"]].apply(
                lambda x: round(x / scale, 2)
            )

        df.rename(
            columns={
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "t": "time",
                "v": "volume",
            },
            inplace=True,
        )
        return df[df["time"] >= start_dt].reset_index(drop=True)

    @wrap_errors("Lấy sổ lệnh thất bại: {error}")
    def intraday(self) -> pd.DataFrame:
        """Dữ liệu khớp lệnh trong ngày. / Intraday matched ticks.

        Returns:
            pd.DataFrame khớp lệnh / intraday ticks.
        """
        headers = make_headers(REFERER_VIETCAP_FLAT)
        payload = {
            "symbol": self._krx_symbols([self.symbol])[0],
            "limit": MAX_PAGE_SIZE,
            "truncTime": None,
        }
        url = f"{TRADING_URL}/market-watch/LEData/getAll"
        response = NET.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        if not data:  # chưa có lệnh khớp / no trades yet
            return pd.DataFrame()
        data = json_normalize(data)
        data = data[
            [  # "id",
                "symbol",
                "matchType",
                "matchVol",
                "matchPrice",
                "truncTime",
            ]
        ]
        data.rename(
            columns={
                "matchType": "action",
                "matchVol": "vol",
                "matchPrice": "price",
                "truncTime": "date",
            },
            inplace=True,
        )
        data["vol"] = pd.to_numeric(data["vol"], errors="coerce").astype("Int64")
        # Phái sinh có giá lẻ (1857.3) nên giữ float. / Derivative prices are fractional.
        data["price"] = pd.to_numeric(
            data["price"], errors="coerce"
        ) / _price_scale(self.symbol)
        data["action"] = data["action"].replace(
            {"b": "buy", "s": "sell", "unknown": "ATO/ATC"}
        )
        data["date"] = (
            pd.to_datetime(
                pd.to_numeric(data["date"], errors="coerce"),
                unit="s",
                utc=True,
                errors="coerce",
            )
            .dt.tz_convert("Asia/Ho_Chi_Minh")
            .dt.tz_localize(None)
            .dt.floor("s")
        )
        data = data.sort_values("date", ascending=True).reset_index(drop=True)
        return data

    @staticmethod
    def _board_items(symbols: list) -> list:
        """Dữ liệu thô bảng giá, bỏ mã không tồn tại. / Raw board rows, unknown codes dropped."""
        url = f"{TRADING_URL}/price/symbols/getList"
        payload = {"symbols": [s.upper() for s in symbols]}
        response = NET.post(
            url, headers=make_headers(REFERER_VIETCAP_STOCK), data=json.dumps(payload)
        )
        return [
            it
            for it in response.json()
            if (it.get("listingInfo") or {}).get("stockType")
        ]

    @staticmethod
    def _krx_symbols(symbols: list) -> list:
        """Đổi mã phái sinh kiểu cũ (VN30F1M) sang mã KRX (41I1GA000); mã khác giữ nguyên.

        Khớp lệnh và giá khớp trên bảng giá chỉ có khi gọi bằng mã KRX.
        """
        symbols = [s.upper() for s in symbols]
        old = [s for s in symbols if _is_derivative(s) and not s.startswith("4")]
        if not old:
            return symbols
        mapping = {
            it["listingInfo"]["symbol"]: it["listingInfo"].get("ticker")
            or it["listingInfo"]["symbol"]
            for it in stock_market._board_items(old)
        }
        return [mapping.get(s, s) for s in symbols]

    @staticmethod
    @wrap_errors("Lấy bảng giá thất bại: {error}")
    def price_board(symbols: list) -> pd.DataFrame:
        """Bảng giá nhiều mã: cổ phiếu, ETF, chứng quyền, trái phiếu, phái sinh.
        / Price board for stocks, ETFs, warrants, bonds and futures.

        Args:
            symbols: danh sách mã, vd ["ACB", "E1VFVN30", "VN30F1M"] / list of codes.
        Returns:
            pd.DataFrame mỗi mã một dòng; giá nghìn VND (phái sinh: điểm),
            giá trị khớp triệu VND / one row per code.
        """
        rows = []
        items = stock_market._board_items(stock_market._krx_symbols(symbols))
        for item in items:
            li, m = item["listingInfo"], item["matchPrice"]
            scale = 1 if li["stockType"] == "FU" else 1000
            row = {
                "symbol": li["symbol"],
                "mappingSymbol": li.get("mappingSymbol"),
                "stockType": li["stockType"],
                "exchange": li.get("board"),
                "organName": li.get("organName"),
                "ceiling": li.get("ceiling"),
                "floor": li.get("floor"),
                "refPrice": li.get("refPrice"),
                "openPrice": m.get("openPrice"),
                "highest": m.get("highest"),
                "lowest": m.get("lowest"),
                "matchPrice": m.get("matchPrice"),
                "matchVol": m.get("matchVol"),
                "avgMatchPrice": m.get("avgMatchPrice"),
                "accumulatedVolume": m.get("accumulatedVolume"),
                "accumulatedValue": m.get("accumulatedValue"),
                "foreignBuyVolume": m.get("foreignBuyVolume"),
                "foreignSellVolume": m.get("foreignSellVolume"),
                "currentRoom": m.get("currentRoom"),
                "openInterest": m.get("openInterest"),
            }
            bid_ask = item.get("bidAsk") or {}
            for side in ["bid", "ask"]:
                levels = bid_ask.get(f"{side}Prices") or []
                for i in range(3):
                    level = levels[i] if i < len(levels) else {}
                    row[f"{side}{i + 1}Price"] = level.get("price")
                    row[f"{side}{i + 1}Vol"] = level.get("volume")

            price_cols = [
                "ceiling",
                "floor",
                "refPrice",
                "openPrice",
                "highest",
                "lowest",
                "matchPrice",
                "avgMatchPrice",
                "bid1Price",
                "bid2Price",
                "bid3Price",
                "ask1Price",
                "ask2Price",
                "ask3Price",
            ]
            for col in price_cols:
                if row[col] is not None:
                    row[col] = round(row[col] / scale, 2)
            rows.append(row)
        return pd.DataFrame(rows)

    @wrap_errors("Lấy sổ lệnh thất bại: {error}")
    def intraday_order(self) -> pd.DataFrame:
        """Thống kê lệnh lớn trong ngày. / Intraday big-order stats.

        Returns:
            pd.DataFrame sổ lệnh lớn / big-order stats.
        """
        headers = make_headers(REFERER_VIETCAP_FLAT)
        payload = {
            "symbol": self.symbol.upper(),
            "limit": BIG_ORDER_LIMIT,
            "truncTime": None,
            "timeFrame": "ONE_SECOND",
        }
        url = f"{TRADING_URL}/sts-computation/BigOrder/getAll"
        response = NET.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        data = json_normalize(data)
        data = data[
            [
                "symbol",
                "matchType",
                "matchVol",
                "price",
                "total",
                "truncTime",
                "type",
            ]
        ]
        data.rename(
            columns={"matchVol": "vol", "matchType": "action", "truncTime": "date"},
            inplace=True,
        )
        data["action"] = data["action"].replace({"b": "buy", "s": "sell"})
        data["price"] = data["price"].astype(float)
        data["price"] = data["price"].apply(lambda x: round(x / 1000, 2))
        data["date"] = (
            pd.to_datetime(data["date"], unit="s", utc=True, errors="coerce")
            .dt.tz_convert("Asia/Ho_Chi_Minh")
            .dt.tz_localize(None)
            .dt.floor("s")
        )
        int_cols = ["vol", "total"]
        data[int_cols] = (
            data[int_cols].apply(pd.to_numeric, errors="coerce").astype("Int64")
        )
        data = data.sort_values("date", ascending=True).reset_index(drop=True)
        return data
