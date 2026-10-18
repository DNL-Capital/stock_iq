# stockiq – Dữ liệu tài chính cho Python

## Cài đặt

`stockiq` hỗ trợ Python 3.9 trở lên. Mở Terminal, PowerShell hoặc Command Prompt và chạy:

```bash
pip install stockiq
```

## Cập nhật

Để cài phiên bản mới nhất đã phát hành trên PyPI:

```bash
pip install --upgrade stockiq
```

## Giới thiệu

`stockiq` là thư viện Python cung cấp dữ liệu tài chính và công cụ phân tích thị trường chứng khoán, quỹ đầu tư, hàng hóa và kinh tế vĩ mô. Thư viện thuộc sở hữu của **DNLcapital**.

Bạn có thể dùng `stockiq` để lấy dữ liệu cổ phiếu Việt Nam, bảng giá, chỉ số, quỹ đầu tư, kinh tế vĩ mô, hàng hóa, tỷ giá và vàng. Kết quả của mỗi hàm công khai là một `pandas.DataFrame`, phù hợp để lọc, tính toán hoặc vẽ biểu đồ bằng Python.

## Bắt đầu nhanh

Nhập nhóm dữ liệu cần dùng từ `stockiq`, rồi gọi hàm trực tiếp trên nhóm đó:

```python
from stockiq import stock, fund, macro_economic

# Lịch sử giá cổ phiếu ACB theo ngày
gia_acb = stock.get_history(
    symbol="ACB",
    interval="days",
    start="2024-01-02",
    end="2024-01-10",
)

# Giá trị tài sản ròng của quỹ BMFF
nav_bmff = fund.get_nav_history(
    fund="BMFF",
    start="2023-03-01",
    end="2024-01-01",
)

# GDP Việt Nam theo năm
gdp = macro_economic.get_general("GDP", "years", "2021", "2024")

print(gia_acb.head())
print(nav_bmff.head())
print(gdp.head())
```

Các hàm có dạng `<nhóm>.get_<tên>(...)`; bạn không cần tạo đối tượng trước khi gọi. Việc lấy dữ liệu từ nguồn cần kết nối mạng.

## Chọn nhóm dữ liệu

| Bạn cần | Nhóm API | Bắt đầu với |
| --- | --- | --- |
| Giá, giao dịch, tài chính và tin tức cổ phiếu | `stock` | `stock.get_history(...)` |
| Bảng giá và lịch sự kiện toàn thị trường | `market` | `market.get_price_board(...)` |
| Chỉ số chứng khoán Việt Nam | `indice` | `indice.get_market(...)` |
| Danh sách, NAV và danh mục quỹ | `fund` | `fund.get_listing()` |
| Chỉ tiêu kinh tế vĩ mô Việt Nam | `macro_economic` | `macro_economic.get_general(...)` |
| Hàng hóa và một số tài sản quốc tế | `commodity` | `commodity.get_index()` |
| Chỉ số chứng khoán thế giới | `global_exchange` | `global_exchange.get_index()` |
| Tỷ giá Vietcombank | `exchange_rate` | `exchange_rate.get_vcb()` |
| Giá vàng, bạc SJC và BTMC | `gold` | `gold.get_sjc()` |

## Tra cứu API theo nhu cầu

### Giá và giao dịch cổ phiếu

```python
from stockiq import stock

gia_thang = stock.get_price_history(
    symbol="ACB", interval="months", start="2023-01", end="2023-12"
)
khoi_ngoai = stock.get_foreign_history(
    symbol="ACB", interval="days", start="2024-01-02", end="2024-01-10"
)
```

| Hàm | Kết quả |
| --- | --- |
| `stock.get_stock_info(symbol)` | Thông tin mã, sàn, ngành; có thể lọc theo `exchange` (`HOSE`, `HNX`, `UPCOM`). |
| `stock.get_history(symbol, interval, start, end)` | Lịch sử OHLCV theo `minutes`, `hours`, `days` hoặc `months`. |
| `stock.get_intraday(symbol)` | Các lệnh khớp trong ngày. |
| `stock.get_intraday_order(symbol)` | Lệnh khớp phân loại theo nhà đầu tư. |
| `stock.get_price_history(symbol, interval, start, end)` | Giá và khối lượng theo kỳ. |
| `stock.get_price_history_summary(symbol, interval)` | Tổng và trung bình của dữ liệu giá. |
| `stock.get_foreign_history(symbol, interval, start, end)` | Giao dịch khối ngoại. |
| `stock.get_foreign_history_summary(symbol, interval)` | Tổng và trung bình giao dịch khối ngoại. |
| `stock.get_proprietary_history(symbol, interval, start, end)` | Giao dịch tự doanh. |
| `stock.get_proprietary_history_summary(symbol, interval)` | Tổng và trung bình giao dịch tự doanh. |
| `stock.get_demand_history(symbol, interval, start, end)` | Cung, cầu và lệnh chưa khớp. |

Với các hàm lịch sử giá, khối ngoại, tự doanh và cung cầu, `interval` nhận `days`, `months`, `quarters` hoặc `years`; `start` và `end` là bắt buộc. Dùng `YYYY-MM-DD` cho ngày, `YYYY-MM` cho tháng và `YYYY` cho quý hoặc năm. `get_history` có bộ khoảng thời gian riêng như trong bảng.

`get_history` và `get_intraday` cũng hỗ trợ ETF, chứng quyền, trái phiếu và phái sinh, ví dụ `E1VFVN30`, `CACB2515`, `BAB124016`, `VN30F1M`.

### Báo cáo tài chính cổ phiếu

```python
from stockiq import stock

can_doi = stock.get_balance_sheet(symbol="ACB", interval="years")
thuyet_minh = stock.get_note(symbol="ACB", interval="quarters")
```

Các hàm sau nhận `symbol` và `interval` là `years` hoặc `quarters`:

| Hàm | Kết quả |
| --- | --- |
| `stock.get_finance_ratio(...)` | Chỉ số tài chính. |
| `stock.get_balance_sheet(...)` | Bảng cân đối kế toán. |
| `stock.get_income_statement(...)` | Báo cáo kết quả kinh doanh. |
| `stock.get_cash_flow(...)` | Báo cáo lưu chuyển tiền tệ. |
| `stock.get_note(...)` | Thuyết minh báo cáo tài chính. |

### Cổ đông, tin tức và sự kiện doanh nghiệp

| Hàm | Kết quả |
| --- | --- |
| `stock.get_shareholders_info(symbol)` | Danh sách và tỷ lệ sở hữu của cổ đông. |
| `stock.get_shareholders_structure(symbol)` | Cơ cấu sở hữu. |
| `stock.get_shareholders_relationship(symbol)` | Công ty con và công ty liên kết. |
| `stock.get_insider_trans(symbol)` | Giao dịch nội bộ. |
| `stock.get_news(symbol)` | Tin tức liên quan đến mã. |
| `stock.get_dividend(symbol, start=None, end=None)` | Cổ tức và lịch chi trả. |
| `stock.get_general_meeting(symbol, start=None, end=None)` | Lịch họp đại hội cổ đông. |
| `stock.get_other_event(symbol, start=None, end=None)` | Niêm yết và các sự kiện khác. |

Ba hàm sự kiện nhận `start` và `end` tùy chọn; khi bỏ trống, chúng lấy dữ liệu 30 ngày gần nhất.

```python
from stockiq import stock

co_dong = stock.get_shareholders_info(symbol="ACB")
co_tuc = stock.get_dividend(
    symbol="ACB", start="2024-01-01", end="2024-12-31"
)
```

### Bảng giá và sự kiện toàn thị trường

```python
from stockiq import market

bang_gia = market.get_price_board(symbols=["ACB", "E1VFVN30", "VN30F1M"])
lich_su_kien = market.get_event_calendar(
    start="2026-10-01", end="2026-10-31", event_codes=["DIV", "AGME"]
)
```

| Hàm | Kết quả |
| --- | --- |
| `market.get_price_board(symbols)` | Bảng giá nhiều mã, gồm giá, khối lượng, mức mua/bán và giao dịch nước ngoài. `accumulatedValue` tính bằng triệu VND. |
| `market.get_event_calendar(start, end, event_codes=None)` | Sự kiện theo khoảng ngày; dùng `event_codes` để lọc loại sự kiện. |

Mã sự kiện gồm `DIV`, `ISS`, `AGME`, `EGME`, `AIS`, `NLIS`, `MOVE`, `SUSP`, `MA`, `DDIND`, `DDINS`, `DDRP` và `OTHE`. Mỗi lần gọi trả tối đa 20.000 sự kiện; hãy chia nhỏ khoảng ngày khi cần lấy nhiều hơn.

### Chỉ số chứng khoán Việt Nam

```python
from stockiq import indice

vnindex = indice.get_market(
    indice="VNINDEX", start="2024-01-01", end="2025-01-01"
)
```

`indice.get_market(indice, start, end)` lấy lịch sử chỉ số. Một số mã thường dùng: `VNINDEX`, `VN30`, `HNXINDEX`, `UPINDEX`, `HNX30`, `VN100`, `VNMIDCAP`, `VNDIAMOND`, `VNFINLEAD`.

### Quỹ đầu tư

Hãy gọi `fund.get_listing()` để xem danh sách và chọn mã quỹ trước khi lấy NAV hoặc danh mục.

```python
from stockiq import fund

danh_sach = fund.get_listing()
nav = fund.get_nav_history(
    fund="BMFF", start="2023-03-01", end="2024-01-01"
)
danh_muc = fund.get_top_holding(fund="BMFF")
```

| Hàm | Kết quả |
| --- | --- |
| `fund.get_listing()` | Danh sách quỹ. |
| `fund.get_nav_history(fund, start=None, end=None)` | Lịch sử giá trị tài sản ròng (NAV). |
| `fund.get_top_holding(fund)` | Các khoản nắm giữ lớn. |
| `fund.get_asset_holding(fund)` | Phân bổ theo loại tài sản. |
| `fund.get_industries_holding(fund)` | Phân bổ theo ngành. |

Tham số `fund` nhận mã như `BMFF` hoặc ID như `87`. Quỹ chưa công bố danh mục có thể cho kết quả rỗng ở `get_top_holding`.

### Kinh tế vĩ mô Việt Nam

```python
from stockiq import macro_economic

gdp = macro_economic.get_general("GDP", "years", "2021", "2024")
cpi = macro_economic.get_general("CPI", "months", "2023-01", "2023-06")
```

`macro_economic.get_general(indicator, interval, start, end)` nhận ký hiệu chỉ tiêu hoặc ID trong bảng:

| ID | Ký hiệu | Chỉ tiêu | `interval` |
| ---: | --- | --- | --- |
| 43 | `GDP` | Tổng sản phẩm quốc nội | `quarters`, `years` |
| 52 | `CPI` | Chỉ số giá tiêu dùng | `months`, `years` |
| 46 | `IIP` | Sản xuất công nghiệp | `months`, `years` |
| 47 | `RET` | Bán lẻ | `months`, `quarters`, `years` |
| 48 | `TRADE` | Xuất nhập khẩu | `months`, `years` |
| 50 | `FDI` | Đầu tư trực tiếp nước ngoài | `months`, `years` |
| 51 | `CREDIT` | Tín dụng | `months`, `years` |
| 53 | `FX` | Tỷ giá | `days`, `years` |
| 55 | `LABOR` | Dân số và lao động | `years` |

Ngày đầu vào có thể ở dạng `YYYY-MM-DD`; với dữ liệu tháng hoặc năm, bạn cũng có thể dùng `YYYY-MM` hoặc `YYYY` tương ứng.

### Hàng hóa, chỉ số thế giới, tỷ giá và vàng

```python
from stockiq import commodity, global_exchange, exchange_rate, gold

hang_hoa = commodity.get_index()
chi_so_the_gioi = global_exchange.get_index()
ty_gia = exchange_rate.get_vcb(date="2023-12-26")
gia_vang_sjc = gold.get_sjc(date="2016-01-04")
gia_vang_btmc = gold.get_btmc()
```

| Hàm | Kết quả |
| --- | --- |
| `commodity.get_index()` | Dầu thô, vàng, bạc, đồng, gạo, VND/USD, lợi suất trái phiếu Mỹ 10 năm, Bitcoin và Ethereum. |
| `global_exchange.get_index()` | Các chỉ số chứng khoán thế giới như Dow Jones, S&P 500, NASDAQ, DAX, Nikkei 225 và Hang Seng. |
| `exchange_rate.get_vcb(date=None)` | Tỷ giá mua tiền mặt, mua chuyển khoản và bán tại Vietcombank. |
| `gold.get_sjc(date=None)` | Giá mua/bán vàng SJC theo chi nhánh và ngày. |
| `gold.get_btmc()` | Giá mua/bán vàng và bạc BTMC mới nhất theo sản phẩm. |

`date` mặc định là hôm nay. `get_vcb` có thể trả `DataFrame` rỗng khi ngày đó không có dữ liệu; `gold.get_sjc` không nhận ngày trong tương lai.

## Quy ước kết quả và lỗi

| Nội dung | Cách dùng |
| --- | --- |
| Ngày | Hầu hết tham số `start`, `end`, `date` dùng `YYYY-MM-DD`. Các ngoại lệ theo kỳ được ghi ngay tại từng nhóm API. |
| Kết quả | Mỗi hàm công khai trả về `pandas.DataFrame`. Dữ liệu có thể rỗng nếu nguồn không có bản ghi phù hợp. |
| Cột thời gian | Dữ liệu ngày thường dùng `datetime64`; chuỗi cổ phiếu theo tháng, quý hoặc năm có thể dùng nhãn kỳ như `2024-01`, `Q1 2024`, `2024`. |
| Tên cột | Dữ liệu thị trường thường dùng tên tiếng Anh như `symbol`, `date`; báo cáo tài chính giữ tên chỉ tiêu tiếng Việt cùng cột `Năm` hoặc `Quý`. |
| Lỗi | `InvalidParameterError` cho tham số không hợp lệ; `DataFetchError` khi lấy hoặc đọc dữ liệu nguồn thất bại. Cả hai kế thừa `stockiqError`. |

## Sở hữu và giấy phép

`stockiq` thuộc sở hữu của **DNLcapital** và được phát hành theo giấy phép MIT. Xem tệp `LICENSE` trong mã nguồn để biết điều khoản sử dụng.
