import json
from typing import Union

import pandas as pd

from ...core._http import NET
from ...core.constants import (
    MAYBANK_URL,
    REFERER_MAYBANK,
    make_headers,
)
from ...core.exceptions import InvalidParameterError, wrap_errors
from ...core.utils import parse_date

_INDICATORS = {
    43: {"name": "GDP", "symbol": "GDP"},
    52: {"name": "CPI", "symbol": "CPI"},
    46: {"name": "Sản xuất công nghiệp", "symbol": "IIP"},
    47: {"name": "Bán lẻ", "symbol": "RET"},
    48: {"name": "Xuất nhập khẩu", "symbol": "TRADE"},
    50: {"name": "FDI", "symbol": "FDI"},
    51: {"name": "Tín dụng", "symbol": "CREDIT"},
    53: {"name": "Tỷ giá", "symbol": "FX"},
    55: {"name": "Dân số và lao động", "symbol": "LABOR"},
}
# Cho phép gõ thường, viết tắt hoặc tiếng Việt. / Case-insensitive names and symbols.
_ALIASES = {}
for _id, _v in _INDICATORS.items():
    _ALIASES[_v["name"].lower()] = _id
    _ALIASES[_v["symbol"].lower()] = _id

# Mã loại kỳ của nguồn. / Source period-type codes.
_PERIODS = {1: "days", 2: "months", 3: "quarters", 4: "years"}


def _indicator_id(indicator) -> int:
    """Tên, symbol hoặc mã số của chỉ số -> mã số. / Indicator name, symbol or id -> id."""
    if isinstance(indicator, (int, float)):
        return int(indicator)
    name = str(indicator).strip().lower()
    if name.isdigit():
        return int(name)
    if name in _ALIASES:
        return _ALIASES[name]
    raise InvalidParameterError(
        f"indicator={indicator!r} không hợp lệ. "
        f"Chọn một trong: {sorted(v['symbol'] for v in _INDICATORS.values())}"
    )


def _period_type(interval) -> int:
    """Tên hoặc mã của loại kỳ -> mã loại kỳ. / Period name or code -> period code."""
    if isinstance(interval, (int, float)):
        code = int(interval)
    else:
        name = str(interval).strip().lower()
        code = (
            int(name)
            if name.isdigit()
            else next((k for k, v in _PERIODS.items() if v == name), None)
        )
    if code not in _PERIODS:
        raise InvalidParameterError(
            f"interval={interval!r} không hợp lệ. Chọn một trong: {list(_PERIODS.values())}"
        )
    return code


def _year_month(value, name: str, need_month: bool = False) -> tuple:
    """"YYYY", "YYYY-MM" hoặc "YYYY-MM-DD" -> (năm, tháng hoặc None).
    / "YYYY", "YYYY-MM" or "YYYY-MM-DD" -> (year, month or None).
    """
    text = str(value).strip()
    parts = text.split("-")
    valid = len(parts) <= 3 and len(parts[0]) == 4 and all(p.isdigit() for p in parts)
    if valid and len(parts) == 3:
        parse_date(text, name)
    valid = valid and (len(parts) < 2 or 1 <= int(parts[1]) <= 12)
    if not valid or (need_month and len(parts) < 2):
        expected = "YYYY-MM hoặc YYYY-MM-DD" if need_month else "YYYY, YYYY-MM hoặc YYYY-MM-DD"
        raise InvalidParameterError(f"{name}={value!r} không hợp lệ. Dùng {expected}.")
    return parts[0], (parts[1] if len(parts) > 1 else None)


class macro_economic:
    def __init__(self, indicator: Union[int, str]):
        """Truy vấn chỉ số kinh tế vĩ mô (theo tên hoặc mã). / Macro-economic accessor."""
        self.indicator = indicator

    @wrap_errors("[{self.indicator}] Lấy dữ liệu vĩ mô thất bại: {error}")
    def general(
        self, interval: Union[int, str], start: Union[int, str], end: Union[int, str]
    ) -> pd.DataFrame:
        """Dữ liệu vĩ mô theo chỉ số / kỳ / khoảng thời gian. / Macro data by indicator, period and range.

        Args:
            interval: days/months/quarters/years (tên hoặc mã 1-4) / period type.
            start: thời điểm bắt đầu: "YYYY-MM-DD" (mọi kỳ); với years/quarters có thể
                chỉ "YYYY", với months có thể "YYYY-MM" / start point.
            end: thời điểm kết thúc, cùng định dạng với start / end point.
        Returns:
            pd.DataFrame vĩ mô / macro data.
        """
        headers = make_headers(REFERER_MAYBANK)

        indicator_id = _indicator_id(self.indicator)
        period_type = _period_type(interval)

        if period_type == 1:  # ngày: cần ngày đầy đủ / days need a full date
            parse_date(start, "start")
            parse_date(end, "end")
            from_year, to_year = start[:4], end[:4]
            from_part, to_part = start, end
        elif period_type == 2:  # tháng / months
            from_year, from_part = _year_month(start, "start", need_month=True)
            to_year, to_part = _year_month(end, "end", need_month=True)
        else:  # quý, năm: chỉ dùng phần năm / quarters, years use the year only
            from_year = _year_month(start, "start")[0]
            to_year = _year_month(end, "end")[0]
            from_part, to_part = (1, 4) if period_type == 3 else (0, 0)

        payload = {
            "type": period_type,
            "fromYear": from_year,
            "toYear": to_year,
            "from": from_part,  # (tháng hoặc quý) (ngày thì nhập đầy đủ)
            "to": to_part,  # (tháng hoặc quý) (ngày thì nhập đầy đủ)
            "normTypeID": indicator_id,
        }

        url = f"{MAYBANK_URL}/reportdatatopbynormtype"
        response = NET.post(url, headers=headers, data=json.dumps(payload))
        data = pd.json_normalize(response.json())

        # GDP #Sản xuất công nghiệp #bán lẻ năm #tín dụng năm #dân số lao động
        if (indicator_id in [43, 46, 48, 55]) or (
            indicator_id in [47, 51, 53] and period_type == 4
        ):
            if indicator_id == 43:
                data = data[~data["ReportTime"].str.contains("tháng", na=False)]

            if indicator_id == 48:
                xuatkhaum = [358, 359, 360, 361, 362, 364, 365, 366, 367, 462]
                xuatkhauy = [
                    85,
                    86,
                    87,
                    88,
                    89,
                    90,
                    91,
                    92,
                    93,
                    94,
                    95,
                    96,
                    97,
                    98,
                    99,
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    108,
                    109,
                    110,
                    111,
                    112,
                    414,
                ]
                data["GroupName"] = data["NormID"].apply(
                    lambda x: (
                        "Xuất khẩu" if x in (xuatkhauy + xuatkhaum) else "Nhập khẩu"
                    )
                )

            if indicator_id == 51:
                data = data.loc[data["GroupName"] != "So với GDP"]
                data["GroupName"] = data["GroupName"].apply(
                    lambda x: "Giá trị" if x == "" else x
                )
                data = data.loc[
                    (data["NormName"] == "Cung tiền M2")
                    | (data["NormName"] == "Tín dụng")
                ]

            if indicator_id == 55:
                laodong = [256, 260, 259, 258, 257, 254, 495, 494, 493, 249]
                data["GroupName"] = data["NormID"].apply(
                    lambda x: "Lao động" if x in laodong else "Dân số"
                )

            data = data.drop(
                columns=[
                    "ReportDataID",
                    "TermID",
                    "TermYear",
                    "TernDay",
                    "NormID",
                    "CssStyle",
                    "NormTypeID",
                    "FromSource",
                    "NormGroupID",
                ]
            )
            data = data.rename(
                columns={
                    "GroupName": "indexGroup",
                    "NormName": "index",
                    "UnitCode": "unit",
                    "NormValue": "value",
                    "ReportTime": "reportTime",
                }
            ).fillna(0)

        # CPI #FDI # bán lẻ tháng #Tín dụng tháng #tỉ giá lãi suất ngày
        if (
            (indicator_id in [52, 50])
            or (indicator_id in [47, 51] and period_type == 2)
            or (indicator_id in [53] and period_type == 1)
        ):
            if indicator_id == 50:
                data = data.loc[
                    (data["NormName"] == "Giải ngân")
                    | (data["NormName"] == "Đăng ký")
                ]

            if indicator_id == 53:
                data = data.loc[data["NormValue"].notna()]

            data = data.drop(
                columns=[
                    "ReportDataID",
                    "TermID",
                    "TermYear",
                    "TernDay",
                    "NormID",
                    "CssStyle",
                    "NormTypeID",
                    "FromSource",
                    "NormGroupID",
                    "GroupName",
                ]
            )
            data = data.rename(
                columns={
                    "NormName": "index",
                    "UnitCode": "unit",
                    "NormValue": "value",
                    "ReportTime": "reportTime",
                }
            ).fillna(0)

        if "indexGroup" in data.columns:
            pivot_data = data.pivot(
                index=["indexGroup", "index", "unit"],
                columns="reportTime",
                values="value",
            ).reset_index()
        else:
            pivot_data = data.pivot(
                index=["index", "unit"], columns="reportTime", values="value"
            ).reset_index()
        pivot_data.columns.name = None
        return pivot_data
