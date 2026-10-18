import json

import pandas as pd
from pandas import json_normalize

from ...core._http import NET
from ...core.constants import REFERER_VIETCAP_STOCK, TRADING_URL, make_headers
from ...core.exceptions import wrap_errors


@wrap_errors()
def _fetch_global_prices(symbols: list, names: dict) -> pd.DataFrame:
    """Giá các mã quốc tế theo danh sách, sắp xếp theo % thay đổi giảm dần.
    / Global prices for ``symbols``, labelled by ``names``, sorted by % change.
    """
    headers = make_headers(REFERER_VIETCAP_STOCK)
    payload = {"symbols": symbols}
    url = f"{TRADING_URL}/price/globalPrice/getList"
    response = NET.post(url, headers=headers, data=json.dumps(payload))
    data = json_normalize(response.json())
    data = data[["id", "exchange", "price", "change", "changePercent"]]
    data = data.rename(
        columns={
            "id": "index",
            "price": "value",
            "changePercent": "ratioChange",
        }
    )
    data["index"] = data["index"].replace(names)
    return data.sort_values("ratioChange", ascending=False).reset_index(drop=True)


class commodity:
    _SYMBOLS = [
        "CL=F", "GC=F", "SI=F", "HG=F", "ZR=F",
        "VND=X", "^TNX", "BTC-USD", "ETH-USD",
    ]
    _NAMES = {
        "CL=F": "Dầu thô",
        "GC=F": "Vàng",
        "SI=F": "Bạc",
        "HG=F": "Đồng",
        "ZR=F": "Gạo",
        "VND=X": "VND/USD",
        "^TNX": "TP Mỹ 10 năm(%)",
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
    }

    @staticmethod
    def get_index() -> pd.DataFrame:
        """Giá hàng hóa và các tài sản quốc tế khác. / Commodities and other assets."""
        return _fetch_global_prices(commodity._SYMBOLS, commodity._NAMES)


class global_exchange:
    _SYMBOLS = [
        "^DJI", "^GSPC", "^IXIC", "^RUT", "^GDOW",
        "^FTSE", "^STOXX", "^GDAXI", "^FCHI", "FTSEMIB.MI",
        "^ADOW", "^N225", "^HSI", "000001.SS", "^STI",
    ]
    _NAMES = {
        "^DJI": "DOWjones",
        "^GSPC": "S&P500",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell",
        "^GDOW": "Dow Jones Global",
        "^FTSE": "FTSE 100",
        "^STOXX": "STOXX 600",
        "^GDAXI": "DAX",
        "^FCHI": "CAC 40",
        "FTSEMIB.MI": "FTSE MIB",
        "^ADOW": "Asia ASX",
        "^N225": "NIKKEI 225",
        "^HSI": "Hang Seng",
        "000001.SS": "Shanghai",
        "^STI": "Singapore",
    }

    @staticmethod
    def get_index() -> pd.DataFrame:
        """Giá các chỉ số thị trường quốc tế. / Global market indices."""
        return _fetch_global_prices(global_exchange._SYMBOLS, global_exchange._NAMES)
