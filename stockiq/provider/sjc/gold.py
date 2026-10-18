from datetime import datetime
from typing import Optional

import pandas as pd

from ...core._http import NET
from ...core.constants import ORIGIN_SJC, REFERER_SJC, SJC_URL, USER_AGENT
from ...core.exceptions import DataFetchError, InvalidParameterError, wrap_errors
from ...core.utils import parse_date


class sjc_gold:
    @staticmethod
    @wrap_errors()
    def prices(date: Optional[str] = None) -> pd.DataFrame:
        """Giá vàng SJC theo ngày, từng chi nhánh. / SJC gold prices by date and branch.

        Args:
            date: YYYY-MM-DD, mặc định hôm nay / defaults to today.
        Returns:
            pd.DataFrame giá mua/bán từng loại vàng theo chi nhánh / buy and sell price per product and branch.
        """
        if date is None:
            day = datetime.now()
        else:
            day = parse_date(date)
            # SJC trả giá mới nhất cho ngày tương lai, gắn nhãn sai ngày.
            if day.date() > datetime.now().date():
                raise InvalidParameterError(
                    f"date={date!r} ở tương lai. / date is in the future."
                )

        # Cloudflare của SJC chặn request thiếu "Content-Type: application/json"
        # (dù payload là dạng form) và phân biệt hoa/thường tên header: giữ nguyên.
        # SJC's Cloudflare needs this exact, case-sensitive header.
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Referer": REFERER_SJC,
            "Origin": ORIGIN_SJC,
        }
        payload = f"method=GetSJCGoldPriceByDate&toDate={day:%d/%m/%Y}"
        url = f"{SJC_URL}/PriceService.ashx"
        response = NET.post(url, headers=headers, data=payload)
        body = response.json()
        if not body.get("success"):
            raise DataFetchError(f"SJC không trả dữ liệu cho ngày {day:%Y-%m-%d}.")
        if not body.get("data"):
            return pd.DataFrame()

        data = pd.DataFrame(body["data"])
        data = data[["TypeName", "BranchName", "BuyValue", "SellValue"]]
        data.columns = ["name", "branch", "buyPrice", "sellPrice"]
        data["date"] = pd.Timestamp(f"{day:%Y-%m-%d}")
        return data
