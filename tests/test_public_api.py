"""Offline checks for the public interface documented in README.md."""

import inspect

import pandas as pd

import stockiq


PUBLIC_API = {
    "stock": {
        "get_stock_info",
        "get_history",
        "get_intraday",
        "get_intraday_order",
        "get_price_history",
        "get_price_history_summary",
        "get_foreign_history",
        "get_foreign_history_summary",
        "get_proprietary_history",
        "get_proprietary_history_summary",
        "get_demand_history",
        "get_finance_ratio",
        "get_balance_sheet",
        "get_income_statement",
        "get_cash_flow",
        "get_note",
        "get_shareholders_info",
        "get_shareholders_structure",
        "get_shareholders_relationship",
        "get_insider_trans",
        "get_news",
        "get_dividend",
        "get_general_meeting",
        "get_other_event",
    },
    "market": {"get_price_board", "get_event_calendar"},
    "indice": {"get_market"},
    "fund": {
        "get_listing",
        "get_nav_history",
        "get_top_holding",
        "get_asset_holding",
        "get_industries_holding",
    },
    "macro_economic": {"get_general"},
    "commodity": {"get_index"},
    "global_exchange": {"get_index"},
    "exchange_rate": {"get_vcb"},
    "gold": {"get_sjc", "get_btmc"},
}


def test_readme_public_api_is_exported_as_classmethods():
    assert set(stockiq.__all__) == set(PUBLIC_API)

    for class_name, methods in PUBLIC_API.items():
        public_class = getattr(stockiq, class_name)
        assert {
            name for name in dir(public_class) if name.startswith("get_")
        } == methods
        for method_name in methods:
            descriptor = inspect.getattr_static(public_class, method_name)
            assert isinstance(descriptor, classmethod)
            signature = inspect.signature(getattr(public_class, method_name))
            assert signature.return_annotation is pd.DataFrame
