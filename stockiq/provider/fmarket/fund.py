import json
from datetime import datetime
from typing import Optional, Union

import pandas as pd

from ...core._http import NET
from ...core.constants import (
    FMARKET_URL,
    REFERER_FMARKET,
    make_headers,
)
from ...core.exceptions import InvalidParameterError, wrap_errors
from ...core.utils import to_day, to_yyyymmdd


class fund:
    category = {
        "88": "MBAM",
        "87": "BMFF",
        "86": "KDEF",
        "83": "RVPF24",
        "82": "VCBFAIF",
        "81": "ENF",
        "80": "VDEF",
        "79": "TCGF",
        "78": "UVDIF",
        "77": "MDI",
        "76": "LHCDF",
        "75": "VCAMDF",
        "72": "MAFEQI",
        "71": "MAFBAL",
        "70": "VCAMBF",
        "69": "GFMVIF",
        "40": "VNDCF",
        "68": "VMPF",
        "67": "VFMVFC",
        "66": "PHVSF",
        "65": "ABBF",
        "64": "LHBF",
        "63": "VCAMFI",
        "62": "HDBOND",
        "61": "PBIF",
        "58": "UVEEF",
        "53": "VLBF",
        "52": "TVPF",
        "51": "ASBF",
        "50": "MAFF",
        "49": "VLGF",
        "47": "MBVF",
        "48": "MBBOND",
        "46": "VCBFMGF",
        "45": "PVBF",
        "41": "TBLF",
        "37": "VNDBF",
        "38": "VNDAF",
        "35": "MAGEF",
        "32": "VCBFBCF",
        "33": "VCBFFIF",
        "31": "VCBFTBF",
        "20": "VEOF",
        "21": "VFF",
        "22": "VIBF",
        "23": "VESAF",
        "27": "VFMVFB",
        "25": "VFMVF4",
        "28": "VFMVF1",
        "12": "BVFED",
        "13": "BVBF",
        "14": "BVPF",
        "29": "DCAF",
        "30": "DFIX",
        "8": "SSIBF",
        "11": "SSISCA",
    }

    headers = make_headers(REFERER_FMARKET)

    def __init__(self, fund: Union[int, str]):
        """Truy vấn dữ liệu chứng chỉ quỹ (theo mã hoặc id). / Fund accessor."""
        self.fund = fund

    def _get_fund_id(self):
        if isinstance(self.fund, (int, float)):
            return int(self.fund)

        if isinstance(self.fund, str):
            fund_str = self.fund.strip()

            if fund_str.isdigit():
                return int(fund_str)

            fund_upper = fund_str.upper()
            matched = [k for k, v in self.category.items() if v == fund_upper]
            if matched:
                return int(matched[0])

        raise InvalidParameterError(f"fund={self.fund!r} không hợp lệ: không tìm thấy quỹ.")

    def _get_fund_code(self):
        fund_id = str(self._get_fund_id())
        return self.category.get(fund_id, "")

    @staticmethod
    # Tổng quan danh sách các quỹ
    @wrap_errors("Không lấy được dữ liệu: {error}")
    def get_listing() -> pd.DataFrame:
        """Danh sách quỹ mở. / Open-fund listing.

        Returns:
            pd.DataFrame danh sách quỹ / fund list.
        """
        payload = {
            "types": ["TRADING_FUND", "NEW_FUND"],
        }
        url = f"{FMARKET_URL}/products/filter"
        response = NET.post(url, headers=fund.headers, data=json.dumps(payload))
        data = pd.json_normalize(response.json()["data"]["rows"])
        lower_col = ["name", "type", "owner.name"]
        for col in lower_col:
            data[col] = data[col].astype(str).str.title()
        data[
            [
                "productNavChange.navTo12Months",
                "productNavChange.annualizedReturn36Months",
            ]
        ] = data[
            [
                "productNavChange.navTo12Months",
                "productNavChange.annualizedReturn36Months",
            ]
        ].fillna(0)
        col_collect = [
            "id",
            "shortName",
            "dataFundAssetType.name",
            "name",
            "type",
            "nav",
            "lastYearNav",
            "productNavChange.navTo12Months",
            "productNavChange.annualizedReturn36Months",
            "owner.name",
            "owner.shortName",
        ]
        data = data[col_collect]
        data = data.rename(
            columns={
                "shortName": "fundSymbol",
                "dataFundAssetType.name": "fundType",
                "productNavChange.navTo12Months": "navLastYear",
                "productNavChange.annualizedReturn36Months": "annualizedReturn",
                "owner.name": "ownerName",
                "owner.shortName": "organName",
            }
        )
        data = data.sort_values("navLastYear", ascending=False)
        return data

    # Tăng trưởng tài sản ròng (NAV) của quỹ
    @wrap_errors("Không lấy được dữ liệu quỹ '{self.fund}': {error}")
    def nav_history(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> pd.DataFrame:
        """Lịch sử NAV theo khoảng ngày. / NAV history over a date range.

        Args:
            start: ngày bắt đầu / start date.
            end: ngày kết thúc / end date.
        Returns:
            pd.DataFrame NAV / nav history.
        """
        start_day = to_yyyymmdd(start, "start") if start is not None else "19700101"
        end_day = (
            to_yyyymmdd(end, "end")
            if end is not None
            else datetime.today().strftime("%Y%m%d")
        )

        payload = {
            "fromDate": start_day,  # "20240620",
            "productId": self._get_fund_id(),
            "toDate": end_day,  # "20250621"
        }

        url = f"{FMARKET_URL}/product/get-nav-history"
        response = NET.post(url, headers=self.headers, data=json.dumps(payload))
        data = pd.json_normalize(response.json()["data"])

        if data.empty:
            return pd.DataFrame()
        else:
            data = (
                data[["productId", "nav", "navDate"]]
                .sort_values("navDate", ascending=True)
                .reset_index(drop=True)
            )

        data["productId"] = data["productId"].astype(str).map(self.category)
        data = data.rename(columns={"productId": "fundSymbol", "navDate": "date"})
        data["date"] = to_day(data["date"])
        return data

    # Phân bổ theo tài sản
    @wrap_errors("Không lấy được dữ liệu quỹ '{self.fund}': {error}")
    def asset_holding(self) -> pd.DataFrame:
        """Phân bổ tài sản của quỹ. / Fund asset allocation.

        Returns:
            pd.DataFrame phân bổ tài sản / asset allocation.
        """
        url = f"{FMARKET_URL}/products/{self._get_fund_id()}"
        response = NET.get(url, headers=self.headers)
        data = pd.json_normalize(response.json()["data"]["productAssetHoldingList"])
        data["fundSymbol"] = self._get_fund_code()
        data = data.drop(
            columns=[
                "id",
                "updateAt",
                "assetType.id",
                "assetType.code",
                "assetType.colorCode",
                "createAt",
            ]
        )
        data = data[["fundSymbol", "assetType.name", "assetPercent"]]
        data = (
            data.rename(
                columns={"assetType.name": "assetType", "assetPercent": "ratio"}
            )
            .sort_values("ratio", ascending=False)
            .reset_index(drop=True)
        )
        return data

    # Phân bổ theo ngành
    @wrap_errors("Không lấy được dữ liệu quỹ '{self.fund}': {error}")
    def industries_holding(self) -> pd.DataFrame:
        """Phân bổ theo ngành. / Industry allocation.

        Returns:
            pd.DataFrame phân bổ ngành / industry allocation.
        """
        url = f"{FMARKET_URL}/products/{self._get_fund_id()}"
        response = NET.get(url, headers=self.headers)
        data = pd.json_normalize(
            response.json()["data"]["productIndustriesHoldingList"]
        )
        data["fundSymbol"] = self._get_fund_code()
        data = data.drop(columns=["id"])[["fundSymbol", "industry", "assetPercent"]]
        data = data.sort_values("assetPercent", ascending=False).reset_index(
            drop=True
        )
        return data

    # Danh mục đầu tư lớn
    @wrap_errors("Không lấy được dữ liệu quỹ '{self.fund}': {error}")
    def top_holding(self) -> pd.DataFrame:
        """Danh mục nắm giữ hàng đầu. / Top holdings.

        Returns:
            pd.DataFrame top nắm giữ / top holdings.
        """
        url = f"{FMARKET_URL}/products/{self._get_fund_id()}"
        response = NET.get(url, headers=self.headers)
        data1 = pd.json_normalize(response.json()["data"]["productTopHoldingList"])
        data2 = pd.json_normalize(
            response.json()["data"]["productTopHoldingBondList"]
        )
        dfs = []
        for df in [data1, data2]:
            if df is not None and not df.empty:
                df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
                if not df.empty:
                    dfs.append(df)

        if not dfs:  # quỹ chưa có danh mục / fund has no holdings
            return pd.DataFrame()

        data = pd.concat(dfs, ignore_index=True)
        data["fundSymbol"] = self._get_fund_code()
        data = data.drop(columns=["id", "updateAt"])
        # Quỹ chỉ có trái phiếu không có cột giá (đã bị dropna ở trên) nên dùng
        # reindex thay vì chọn cột trực tiếp. / Bond-only funds have no price columns.
        data = data.reindex(
            columns=[
                "fundSymbol",
                "type",
                "stockCode",
                "industry",
                "netAssetPercent",
                "price",
                "changeFromPrevious",
                "changeFromPreviousPercent",
            ]
        )
        data["type"] = data["type"].replace({"STOCK": "stock"})
        data.loc[
            data["type"].str.contains("BOND", case=False, na=False), "type"
        ] = "bond"
        data = data.rename(
            columns={
                "stockCode": "symbol",
                "changeFromPrevious": "priceChange",
                "changeFromPreviousPercent": "ratioPriceChange",
            }
        )
        data = (
            data.fillna(0)
            .sort_values("netAssetPercent", ascending=False)
            .reset_index(drop=True)
        )
        has_stock = data["type"].str.contains("stock", case=False, na=False).any()
        has_bond = data["type"].str.contains("bond", case=False, na=False).any()

        # Trái phiếu không có giá nên quỹ chỉ có trái phiếu bỏ các cột giá.
        if has_bond and not has_stock:
            data = data.drop(columns=["price", "priceChange", "ratioPriceChange"])
        return data
