# --- User-Agent (identical across every request) ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)

# --- Referer values ---
# Kept distinct on purpose: different Vietcap endpoints are called with different
# Referer query-strings, and fmarket/maybank are different hosts entirely.
REFERER_VIETCAP = "https://trading.vietcap.com.vn/"
REFERER_VIETCAP_STOCK = (
    "https://trading.vietcap.com.vn/"
    "?filter-group=HOSE&filter-value=HOSE&view-type=FLAT&type=stock"
)
REFERER_VIETCAP_FLAT = (
    "https://trading.vietcap.com.vn/?filter-group=HOSE&filter-value=HOSE&view-type=FLAT"
)
REFERER_FMARKET = "https://fmarket.vn/"
REFERER_MAYBANK = "https://data.maybanktrade.com.vn/du-lieu-vi-mo"
REFERER_SJC = "https://sjc.com.vn/bieu-do-gia-vang"
ORIGIN_SJC = "https://sjc.com.vn"


def make_headers(referer=REFERER_VIETCAP):
    """Standard JSON request headers with a per-endpoint Referer."""
    return {
        "content-type": "application/json",
        "referer": referer,
        "user-agent": USER_AGENT,
    }


# --- Base URLs (the endpoint path is appended at the call site) ---
IQ_URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v1"
EVENT_URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v2"
TRADING_URL = "https://trading.vietcap.com.vn/api"
FMARKET_URL = "https://api.fmarket.vn/res"
MAYBANK_URL = "https://data.maybanktrade.com.vn/data"
VCB_URL = "https://www.vietcombank.com.vn/api"
SJC_URL = "https://sjc.com.vn/GoldPrice/Services"
BTMC_URL = "http://api.btmc.vn/api/BTMCAPI"

# Khóa công khai của API BTMC. / Public BTMC API key.
BTMC_KEY = "3kd8ub1llcg9t45hnoh8hmn7t5kc2v"

# --- Interval maps (two contexts, intentionally kept separate) ---
TIMEFRAME_OHLC = {
    "days": "ONE_DAY",
    "months": "ONE_MONTH",
    "minutes": "ONE_MINUTE",
    "hours": "ONE_HOUR",
}
TIMEFRAME_REPORT = {
    "days": "ONE_DAY",
    "months": "ONE_MONTH",
    "quarters": "ONE_QUARTER",
    "years": "ONE_YEAR",
}

# --- Named magic numbers ---
MAX_PAGE_SIZE = 50_000  # upper bound on rows requested from the source
OHLC_COUNT_BACK = 30_000  # number of OHLC bars to fetch back
BIG_ORDER_LIMIT = 30_000  # rows requested for intraday big-order stats
