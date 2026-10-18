from typing import get_args

import pandas as pd
from pandas import json_normalize

from ...core._http import NET
from ...core.constants import (
    IQ_URL,
    REFERER_VIETCAP_STOCK,
    make_headers,
)
from ...core.exceptions import validate_interval, wrap_errors
from ...core.types import IntervalFinancial

_INTERVALS = get_args(IntervalFinancial)  # ("years", "quarters")


class stock_financial:
    def __init__(self, symbol: str):
        """Truy vấn báo cáo tài chính cho một mã. / Financial-statement accessor."""
        self.symbol = symbol
        self._metrics_cache = None

    def _metrics(self) -> dict:
        """Danh mục chỉ tiêu (mã -> tên) theo mã CK, cache theo instance. / Per-ticker line-item metadata."""
        if self._metrics_cache is None:
            url = f"{IQ_URL}/company/{self.symbol.upper()}/financial-statement/metrics"
            response = NET.get(url, headers=make_headers())
            self._metrics_cache = response.json()["data"]
        return self._metrics_cache

    @staticmethod
    def _column_names(items: list) -> dict:
        """Map mã chỉ tiêu -> tên cột tiếng Việt, giữ thứ tự như trên web.

        Tên trùng nhau được thêm dần tên mục cha ("Cha > Con") cho đến khi
        phân biệt được; nếu vẫn trùng (metrics lặp lại cả nhánh) thì đánh số
        "(2)", "(3)" theo thứ tự xuất hiện.
        """
        by_name = {item["name"]: item for item in items}

        def label(item, depth):
            parts = [item["titleVi"] or item["field"]]
            parent = item.get("parent")
            while depth > 0 and parent in by_name:
                parts.insert(0, by_name[parent]["titleVi"])
                parent = by_name[parent].get("parent")
                depth -= 1
            return " > ".join(parts)

        depths = {item["field"]: 0 for item in items}
        reserved = {"Năm", "Quý"}
        for _ in range(10):
            names = {item["field"]: label(item, depths[item["field"]]) for item in items}
            counts = {}
            for name in names.values():
                counts[name] = counts.get(name, 0) + 1
            dup = [f for f, n in names.items() if counts[n] > 1 or n in reserved]
            if not dup:
                return names
            for f in dup:
                depths[f] += 1

        seen = {}
        for f, n in names.items():
            seen[n] = seen.get(n, 0) + 1
            if seen[n] > 1 or n in reserved:
                names[f] = f"{n} ({seen[n]})"
        return names

    @wrap_errors("Không lấy được dữ liệu cho '{self.symbol}': {error}")
    def _statement(
        self, section: str, interval: IntervalFinancial, headers=None
    ) -> pd.DataFrame:
        """Lấy một báo cáo và đặt tên cột theo metrics. / Fetch one statement, columns named from metrics."""
        validate_interval(interval, _INTERVALS)
        url = f"{IQ_URL}/company/{self.symbol.upper()}/financial-statement?section={section}"
        response = NET.get(url, headers=headers or make_headers())
        data = json_normalize(response.json()["data"][interval])
        if data.empty:
            return pd.DataFrame()

        names = self._column_names(self._metrics()[section])
        fields = [
            f for f in names if f in data.columns and data[f].notna().any()
        ]
        values = data[fields].apply(pd.to_numeric, errors="coerce")
        if section != "NOTE":
            # NOTE có chỉ tiêu tỷ lệ (vd 0.1214) nên giữ float
            values = values.round().astype("Int64")
        values.columns = [names[f] for f in fields]

        year = pd.to_numeric(data["yearReport"], errors="coerce")
        if interval == "quarters":
            quarter = pd.to_numeric(data["lengthReport"], errors="coerce")
            values.insert(
                0,
                "Quý",
                "Q"
                + data["lengthReport"].astype(str)
                + " "
                + data["yearReport"].astype(str),
            )
            order = pd.DataFrame({"y": year, "q": quarter}).sort_values(["y", "q"])
        else:
            values.insert(0, "Năm", year.astype("Int64"))
            order = pd.DataFrame({"y": year}).sort_values(["y"])

        return values.loc[order.index].reset_index(drop=True)

    def balance_sheet(self, interval: IntervalFinancial) -> pd.DataFrame:
        """Bảng cân đối kế toán. / Balance sheet.

        Args:
            interval: years/quarters.
        Returns:
            pd.DataFrame cân đối kế toán / balance sheet.
        """
        return self._statement(
            "BALANCE_SHEET", interval, headers=make_headers(REFERER_VIETCAP_STOCK)
        )

    def income_statement(self, interval: IntervalFinancial) -> pd.DataFrame:
        """Báo cáo kết quả kinh doanh. / Income statement.

        Args:
            interval: years/quarters.
        Returns:
            pd.DataFrame kết quả kinh doanh / income statement.
        """
        return self._statement("INCOME_STATEMENT", interval)

    def cash_flow(self, interval: IntervalFinancial) -> pd.DataFrame:
        """Báo cáo lưu chuyển tiền tệ. / Cash-flow statement.

        Args:
            interval: years/quarters.
        Returns:
            pd.DataFrame lưu chuyển tiền tệ / cash flow.
        """
        return self._statement("CASH_FLOW", interval).fillna(0)

    def note(self, interval: IntervalFinancial) -> pd.DataFrame:
        """Thuyết minh báo cáo tài chính. / Financial-statement notes.

        Args:
            interval: years/quarters.
        Returns:
            pd.DataFrame thuyết minh / notes.
        """
        return self._statement("NOTE", interval)

    @wrap_errors("Không lấy được dữ liệu cho '{self.symbol}': {error}")
    def finance_ratio(self, interval: IntervalFinancial) -> pd.DataFrame:
        """Chỉ số tài chính theo kỳ. / Financial ratios by period.

        Args:
            interval: years/quarters.
        Returns:
            pd.DataFrame chỉ số / ratios.
        """
        validate_interval(interval, _INTERVALS)
        headers = make_headers()

        url = f"{IQ_URL}/company/{self.symbol.upper()}/statistics-financial"
        response = NET.get(url, headers=headers)
        data = response.json()["data"]
        data = pd.json_normalize(data)
        cols = [
            "dividendYield",
            "cashRatio",
            "quickRatio",
            "currentRatio",
            "roe",
            "roa",
            "grossMargin",
            "ebitMargin",
            "preTaxProfitMargin",
            "afterTaxProfitMargin",
            "netInterestMargin",
            "averageYieldOnEarningAssets",
            "averageCostOfFinancing",
            "nonAndInterestIncome",
            "costToIncome",
            "loansGrowth",
            "depositGrowth",
            "ldrLoanDepositRatio",
            "npl",
            "loansLossReservesToNPLs",
            "loansLossReserveToLoans",
            "provisionToOutstandingLoans",
            "roic",
            "car",
            "casaRatio",
        ]
        data[cols] = round(data[cols] * 100, 2)

        if interval == "quarters":
            data = data.loc[data["quarter"] != 5].copy()
            data["_year"] = pd.to_numeric(data["year"], errors="coerce")
            data["_quarter"] = pd.to_numeric(data["quarter"], errors="coerce")
            data["Quý"] = (
                "Q" + data["quarter"].astype(str) + " " + data["year"].astype(str)
            )
            quarter = data.pop("Quý")
            data.insert(1, "Quý", quarter)
            data = data.loc[:, data.notna().any()]
            data = data.sort_values(["_year", "_quarter"]).reset_index(drop=True)
            drop_cols = [
                "year",
                "quarter",
                "ratioTTMId",
                "ratioType",
                "organCode",
                "yearReport",
                "cir",
                "_year",
                "_quarter",
            ]
            exsit_cols = [col for col in drop_cols if col in data.columns]
            data = data.drop(columns=exsit_cols)
        else:
            data = data.loc[data["quarter"] == 5].copy()
            data["_year"] = pd.to_numeric(data["year"], errors="coerce")
            data = data.loc[:, data.notna().any()]
            data = data.sort_values(["_year"]).reset_index(drop=True)
            drop_cols = [
                "quarter",
                "ratioTTMId",
                "ratioType",
                "organCode",
                "yearReport",
                "cir",
                "ratioYearId",
                "_year",
            ]
            exsit_cols = [col for col in drop_cols if col in data.columns]
            data = data.drop(columns=exsit_cols)

        data = data.rename(
            columns={
                "year": "Năm",
                "numberOfSharesMktCap": "Số cp lưu hành (triệu cp)",
                "marketCap": "Vốn hóa",
                "dividendYield": "Tỷ suất cổ tức(%)",
                "pe": "Chỉ số Giá trên Lợi nhuận",
                "pb": "Chỉ số Giá trên Giá trị sổ sách",
                "ps": "Chỉ số Giá trên Doanh thu",
                "priceToCashFlow": "Tỷ giá trên dòng tiền",
                "evToEbitda": "Chỉ số Giá trị doanh nghiệp trên lợi nhuận trước lãi vay, thuế và khấu hao",
                "cashRatio": "Thanh khoản tiền mặt (%)",
                "quickRatio": "Thanh khoản linh động (%)",
                "currentRatio": "Thanh khoản hiện tại (%)",
                "ownersEquity": "Vốn chủ sở hữu",
                "debtPerEquity": "Vay ngắn và dài hạn trên vốn chủ sở hữu",
                "debtToEquity": "Nợ trên vốn chủ sở hữu",
                "roe": "Chỉ số lợi nhuận trên vốn chủ sở hữu (%)",
                "roa": "Chỉ số lợi nhuận trên tổng tài sản (%)",
                "daySaleOutstanding": "Số ngày thu tiền bình quân",
                "daysInventoryOutstanding": "Số ngày tồn kho bình quân",
                "daysPayableOutstanding": "Số ngày thanh toán bình quân",
                "grossMargin": "Biên lợi nhuận gộp (%)",
                "ebitMargin": "Biên lợi nhuận (%)",
                "preTaxProfitMargin": "Biên lợi nhuận trước thuế (%)",
                "afterTaxProfitMargin": "Biên lợi nhuận ròng (%)",
                "assetTurnover": "Vòng quay tài sản",
                "netInterestMargin": "Tỷ suất lợi nhuận ròng(%)",
                "averageYieldOnEarningAssets": "Tỷ suất sinh lời từ tài sản có sinh lãi (%)",
                "averageCostOfFinancing": "Chi phí tài chính trung bình (%)",
                "nonAndInterestIncome": "Thu nhập ngoài lãi và từ lãi (%)",
                "costToIncome": "Chi phí trên thu nhập(%)",
                "loansGrowth": "Tăng trưởng tín dụng (%)",
                "depositGrowth": "Tăng trưởng tiền gửi(%)",
                "equityToLiabilities": "Vốn chủ trên tổng nợ",
                "equityToLoans": "Vốn chủ trên tổng vay",
                "totalEquityTotalAsset": "Vốn chủ trên tài sản",
                "ldrLoanDepositRatio": "Tỷ lệ dư nợ cho vay so với tiền gửi(%)",
                "npl": "Tỷ lệ nợ xấu(%)",
                "loansLossReservesToNPLs": "Dự phòng rủi ro tín dụng trên nợ xấu (%)",
                "loansLossReserveToLoans": "Dự phòng rủi ro tín dụng trên cho vay(%)",
                "provisionToOutstandingLoans": "Trích lập dự phòng trên cho vay (%)",
                "ebit": "Lợi nhuận trước lãi vay và thuế",
                "ebitda": "Lợi nhuận trước lãi vay, thuế và khấu hao tài sản",
                "roic": "Tỷ suất sinh lợi trên vốn đầu tư (%)",
                "cashCycle": "Chu kỳ tiền",
                "fixedAssetTurnover": "Vòng quay tài sản cố định",
                "financialLeverage": "Đòng bẩy tài chính",
                "car": "CAR(%)",
                "casaRatio": "Tiền gửi không kỳ hạn(%)",
                "nob66": "Tiền gửi không kỳ hạn",
                "nob69": "Tiền gửi ký quỹ",
                "nob70": "Tiền gửi mục đích riêng",
                "bsb113": "Tiền gửi của khách hàng",
            }
        )

        for col in data.columns:
            if col not in ["Năm", "Quý"]:
                data[col] = pd.to_numeric(data[col], errors="coerce").astype(
                    "float64"
                )

        return data
