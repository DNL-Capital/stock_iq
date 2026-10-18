import base64
import warnings
from datetime import datetime
from io import BytesIO
from typing import Optional

import pandas as pd

from ...core._http import NET
from ...core.constants import USER_AGENT, VCB_URL
from ...core.exceptions import wrap_errors
from ...core.utils import parse_date


class vcb_exchange_rate:
    @staticmethod
    @wrap_errors()
    def rates(date: Optional[str] = None) -> pd.DataFrame:
        """Tỷ giá ngoại tệ Vietcombank theo ngày. / Vietcombank exchange rates by date.

        Args:
            date: YYYY-MM-DD, mặc định hôm nay / defaults to today.
        Returns:
            pd.DataFrame tỷ giá mua/bán từng ngoại tệ / buy and sell rate per currency.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            parse_date(date)

        url = f"{VCB_URL}/exchangerates/exportexcel"
        response = NET.get(
            url, params={"date": date}, headers={"user-agent": USER_AGENT}
        )
        encoded = response.json()["Data"]
        if not encoded:
            return pd.DataFrame()

        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore", UserWarning
            )  # openpyxl: no default style
            data = pd.read_excel(
                BytesIO(base64.b64decode(encoded)),
                sheet_name="ExchangeRate",
                header=None,
            )

        # Dòng tiêu đề/ghi chú nằm quanh bảng; chỉ giữ dòng có mã ngoại tệ.
        data = data.iloc[:, :5]
        data.columns = [
            "currencyCode",
            "currencyName",
            "buyCash",
            "buyTransfer",
            "sell",
        ]
        data = data.loc[
            data["currencyCode"].astype(str).str.fullmatch(r"[A-Z]{3}")
        ].copy()
        for col in ["buyCash", "buyTransfer", "sell"]:
            data[col] = pd.to_numeric(
                data[col].astype(str).str.replace(",", ""), errors="coerce"
            )
        data["date"] = pd.Timestamp(date)
        return data.reset_index(drop=True)
