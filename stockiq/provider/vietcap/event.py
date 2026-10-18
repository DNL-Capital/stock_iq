from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup
from pandas import json_normalize

from ...core._http import NET
from ...core.constants import (
    EVENT_URL,
    IQ_URL,
    MAX_PAGE_SIZE,
    make_headers,
)
from ...core.exceptions import DataFetchError, wrap_errors
from ...core.utils import parse_date, to_day, to_yyyymmdd


def _date_range(start: Optional[str], end: Optional[str]) -> tuple:
    """Đổi start/end "YYYY-MM-DD" sang YYYYMMDD; mặc định 30 ngày gần nhất.
    / Convert start/end to YYYYMMDD; defaults to the last 30 days.
    """
    end_dt = parse_date(end, "end") if end else datetime.today()
    start_dt = parse_date(start, "start") if start else end_dt - timedelta(days=30)
    return start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")


class stock_event:
    def __init__(self, symbol: str):
        """Truy vấn tin tức & sự kiện cho một mã. / News & events accessor."""
        self.symbol = symbol

    @staticmethod
    @wrap_errors()
    def calendar(
        start: str, end: str, event_codes: Optional[list] = None
    ) -> pd.DataFrame:
        """Lịch sự kiện toàn thị trường. / Market-wide corporate-event calendar.

        Args:
            start: ngày bắt đầu "YYYY-MM-DD" / start date.
            end: ngày kết thúc "YYYY-MM-DD" / end date.
            event_codes: lọc loại sự kiện, mặc định tất cả / optional filter:
                DIV cổ tức tiền mặt, ISS phát hành, AGME ĐHCĐ thường niên,
                EGME ĐHCĐ bất thường, AIS niêm yết thêm, NLIS niêm yết mới,
                MOVE chuyển sàn, SUSP tạm dừng niêm yết, MA mua bán sáp nhập,
                DDIND/DDINS/DDRP giao dịch nội bộ, OTHE khác.
        Returns:
            pd.DataFrame sự kiện / events.
        """
        params = {
            "fromDate": to_yyyymmdd(start, "start"),
            "toDate": to_yyyymmdd(end, "end"),
            "size": MAX_PAGE_SIZE,
        }
        if event_codes:
            params["eventCodes"] = ",".join(c.upper() for c in event_codes)

        url = f"{EVENT_URL}/events"
        response = NET.get(url, headers=make_headers(), params=params)
        body = response.json()["data"]
        content = body["content"]
        if body.get("totalElements", 0) > len(content):
            raise DataFetchError(
                f"Khoảng ngày có {body['totalElements']} sự kiện, vượt giới hạn "
                f"{len(content)} mỗi lần gọi; hãy thu hẹp khoảng ngày."
            )
        if not content:
            return pd.DataFrame()

        data = json_normalize(content)
        cols = [
            "ticker",
            "eventCode",
            "eventNameVi",
            "eventTitleVi",
            "publicDate",
            "exrightDate",
            "recordDate",
            "payoutDate",
            "issueDate",
            "startDate",
            "endDate",
            "valuePerShare",
            "exerciseRatio",
        ]
        data = data[[c for c in cols if c in data.columns]]
        for col in [
            "publicDate",
            "exrightDate",
            "recordDate",
            "payoutDate",
            "issueDate",
            "startDate",
            "endDate",
        ]:
            if col in data.columns:
                data[col] = to_day(data[col])
        data = data.rename(
            columns={
                "ticker": "symbol",
                "eventNameVi": "eventName",
                "eventTitleVi": "eventTitle",
            }
        )
        return data.sort_values(["publicDate", "symbol"]).reset_index(drop=True)

    @wrap_errors()
    def news(self) -> pd.DataFrame:
        """Tin tức liên quan đến mã. / Company news.

        Returns:
            pd.DataFrame tin tức / news.
        """
        headers = make_headers()

        now = datetime.today()
        from_date = (now - timedelta(days=30)).strftime("%Y%m%d")
        to_date = now.strftime("%Y%m%d")
        params = {
            "ticker": self.symbol.upper(),
            "fromDate": from_date,
            "toDate": to_date,
            "size": MAX_PAGE_SIZE,
        }

        # Lấy danh sách tin tức
        url = f"{IQ_URL}/news"
        response = NET.get(url, headers=headers, params=params)
        data = json_normalize(response.json()["data"]["content"])
        datax = data[["id", "publicDate", "newsTitle"]]

        # Hàm lấy chi tiết tin
        def fetch_news_detail(news_id):
            try:
                url = f"{IQ_URL}/news/{news_id}"
                response = NET.get(url, headers=headers)
                detail = json_normalize(response.json()["data"])

                html = detail.loc[0, "newsFullContent"]
                source_link = (
                    detail.loc[0, "newsSourceLink"]
                    if "newsSourceLink" in detail.columns
                    else "-"
                )

                # Trích link file PDF từ HTML (nếu có)
                if pd.notna(html):
                    soup = BeautifulSoup(html, "html.parser")
                    link = soup.find("a", href=True)
                    file_url = link.get("href") if link else "-"
                else:
                    file_url = "-"

                return {
                    "id": news_id,
                    "newsFullContent": file_url,
                    "newsSourceLink": source_link,
                }

            except Exception:
                return {
                    "id": news_id,
                    "newsFullContent": "-",
                    "newsSourceLink": "-",
                }

        # Chạy đa luồng lấy chi tiết tin
        results = []
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(fetch_news_detail, _id) for _id in data["id"]
            ]
            for future in as_completed(futures):
                results.append(future.result())

        # Gộp kết quả
        tong = pd.DataFrame(results)
        datax = pd.merge(datax, tong, on="id", how="left")
        datax[["newsSourceLink", "newsFullContent"]] = datax[
            ["newsSourceLink", "newsFullContent"]
        ].fillna("-")
        cols = ["publicDate", "newsTitle", "newsSourceLink", "newsFullContent"]
        datax = datax[cols]
        datax.insert(0, "symbol", self.symbol.upper())
        datax["publicDate"] = pd.to_datetime(
            datax["publicDate"], format="mixed", errors="coerce"
        )
        datax["publicDate"] = datax["publicDate"].dt.floor("s")
        datax = datax[
            ~((datax["newsSourceLink"] == "-") & (datax["newsFullContent"] == "-"))
        ]
        datax["newsTitle"] = datax["newsTitle"].replace(r"^.*?:\s*", "", regex=True)
        rename_dict = {
            "newsTitle": "title",
            "newsSourceLink": "source",
            "newsFullContent": "content",
        }
        datax = datax.rename(columns=rename_dict)
        datax = datax.sort_values("publicDate", ascending=True).reset_index(
            drop=True
        )
        return datax

    @wrap_errors()
    def _events(
        self,
        event_codes: str,
        cols: list,
        start: Optional[str],
        end: Optional[str],
    ) -> pd.DataFrame:
        """Sự kiện của mã theo loại và khoảng ngày; cột ngày là cột kết thúc bằng "Date".
        / Events of this symbol by type and date range; "*Date" columns are parsed and used for sorting.
        """
        from_date, to_date = _date_range(start, end)
        params = {
            "tickers": self.symbol.upper(),
            "fromDate": from_date,
            "toDate": to_date,
            "eventCodes": event_codes,
            "size": MAX_PAGE_SIZE,
        }
        url = f"{EVENT_URL}/events"
        response = NET.get(url, headers=make_headers(), params=params)
        data = json_normalize(response.json()["data"]["content"])
        data = data.reindex(columns=cols)  # rỗng/thiếu cột vẫn chạy
        date_cols = [c for c in cols if c.endswith("Date")]
        for col in date_cols:
            data[col] = to_day(data[col])
        data["eventTitleVi"] = data["eventTitleVi"].replace(
            r"^.*?-\s*", "", regex=True
        )
        data = data.rename(
            columns={
                "ticker": "symbol",
                "eventNameVi": "eventName",
                "eventTitleVi": "eventTitle",
            }
        )
        return data.sort_values(date_cols).reset_index(drop=True)

    def dividend(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> pd.DataFrame:
        """Lịch sử cổ tức. / Dividend history.

        Args:
            start: ngày bắt đầu "YYYY-MM-DD", mặc định 30 ngày trước end / start date.
            end: ngày kết thúc "YYYY-MM-DD", mặc định hôm nay / end date.
        Returns:
            pd.DataFrame cổ tức / dividends.
        """
        cols = ["ticker", "eventNameVi", "eventTitleVi", "publicDate", "exrightDate"]
        return self._events("DIV,ISS", cols, start, end)

    def general_meeting(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> pd.DataFrame:
        """Thông tin đại hội cổ đông. / General-meeting events.

        Args:
            start: ngày bắt đầu "YYYY-MM-DD", mặc định 30 ngày trước end / start date.
            end: ngày kết thúc "YYYY-MM-DD", mặc định hôm nay / end date.
        Returns:
            pd.DataFrame đại hội cổ đông / general meetings.
        """
        cols = [
            "ticker",
            "eventNameVi",
            "eventTitleVi",
            "publicDate",
            "exrightDate",
            "issueDate",
        ]
        return self._events("AGME,AGMR,EGME", cols, start, end)

    def other_event(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> pd.DataFrame:
        """Các sự kiện doanh nghiệp khác. / Other corporate events.

        Args:
            start: ngày bắt đầu "YYYY-MM-DD", mặc định 30 ngày trước end / start date.
            end: ngày kết thúc "YYYY-MM-DD", mặc định hôm nay / end date.
        Returns:
            pd.DataFrame sự kiện khác / other events.
        """
        cols = ["ticker", "eventNameVi", "eventTitleVi", "publicDate", "issueDate"]
        return self._events("AIS,MA,MOVE,NLIS,OTHE,RETU,SUSP", cols, start, end)
