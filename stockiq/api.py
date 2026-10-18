from typing import Optional, Union

import pandas as pd

from .provider.btmc.gold import btmc_gold
from .provider.fmarket.fund import fund as _fund
from .provider.maybank.macro import macro_economic as _macro_economic
from .provider.sjc.gold import sjc_gold
from .provider.vietcap.demand import stock_demand
from .provider.vietcap.event import stock_event
from .provider.vietcap.financial import stock_financial
from .provider.vietcap.foreign import stock_foreign
from .provider.vietcap.global_index import commodity as _commodity
from .provider.vietcap.global_index import global_exchange as _global_exchange
from .provider.vietcap.indice import indice as _indice
from .provider.vietcap.market import stock_market
from .provider.vietcap.price import stock_price
from .provider.vietcap.proprietary import stock_proprietary
from .provider.vietcap.shareholder import stock_shareholder
from .provider.vietcombank.exchange_rate import vcb_exchange_rate


class stock:
    """Dữ liệu cổ phiếu, gọi qua stock.get_xxx(symbol=..., ...). / Stock data via stock.get_xxx(symbol=..., ...)."""

    # ===== MARKET =====
    @classmethod
    def get_stock_info(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_market.stock_info. / See stock_market.stock_info."""
        return stock_market(symbol).stock_info(*args, **kwargs)

    @classmethod
    def get_history(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_market.history. / See stock_market.history."""
        return stock_market(symbol).history(*args, **kwargs)

    @classmethod
    def get_intraday(cls, symbol) -> pd.DataFrame:
        """Xem stock_market.intraday. / See stock_market.intraday."""
        return stock_market(symbol).intraday()

    @classmethod
    def get_intraday_order(cls, symbol) -> pd.DataFrame:
        """Xem stock_market.intraday_order. / See stock_market.intraday_order."""
        return stock_market(symbol).intraday_order()

    @classmethod
    def get_price_history(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_price.price_history. / See stock_price.price_history."""
        return stock_price(symbol).price_history(*args, **kwargs)

    @classmethod
    def get_price_history_summary(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_price.price_history_summary. / See stock_price.price_history_summary."""
        return stock_price(symbol).price_history_summary(*args, **kwargs)

    @classmethod
    def get_foreign_history(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_foreign.foreign_history. / See stock_foreign.foreign_history."""
        return stock_foreign(symbol).foreign_history(*args, **kwargs)

    @classmethod
    def get_foreign_history_summary(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_foreign.foreign_history_summary. / See stock_foreign.foreign_history_summary."""
        return stock_foreign(symbol).foreign_history_summary(*args, **kwargs)

    @classmethod
    def get_proprietary_history(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_proprietary.proprietary_history. / See stock_proprietary.proprietary_history."""
        return stock_proprietary(symbol).proprietary_history(*args, **kwargs)

    @classmethod
    def get_proprietary_history_summary(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_proprietary.proprietary_history_summary. / See stock_proprietary.proprietary_history_summary."""
        return stock_proprietary(symbol).proprietary_history_summary(*args, **kwargs)

    @classmethod
    def get_demand_history(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_demand.demand_history. / See stock_demand.demand_history."""
        return stock_demand(symbol).demand_history(*args, **kwargs)

    # ===== FINANCIAL =====
    @classmethod
    def get_finance_ratio(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_financial.finance_ratio. / See stock_financial.finance_ratio."""
        return stock_financial(symbol).finance_ratio(*args, **kwargs)

    @classmethod
    def get_balance_sheet(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_financial.balance_sheet. / See stock_financial.balance_sheet."""
        return stock_financial(symbol).balance_sheet(*args, **kwargs)

    @classmethod
    def get_income_statement(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_financial.income_statement. / See stock_financial.income_statement."""
        return stock_financial(symbol).income_statement(*args, **kwargs)

    @classmethod
    def get_cash_flow(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_financial.cash_flow. / See stock_financial.cash_flow."""
        return stock_financial(symbol).cash_flow(*args, **kwargs)

    @classmethod
    def get_note(cls, symbol, *args, **kwargs) -> pd.DataFrame:
        """Xem stock_financial.note. / See stock_financial.note."""
        return stock_financial(symbol).note(*args, **kwargs)

    # ===== SHAREHOLDER =====
    @classmethod
    def get_shareholders_info(cls, symbol) -> pd.DataFrame:
        """Xem stock_shareholder.shareholders_info. / See stock_shareholder.shareholders_info."""
        return stock_shareholder(symbol).shareholders_info()

    @classmethod
    def get_shareholders_structure(cls, symbol) -> pd.DataFrame:
        """Xem stock_shareholder.shareholders_structure. / See stock_shareholder.shareholders_structure."""
        return stock_shareholder(symbol).shareholders_structure()

    @classmethod
    def get_shareholders_relationship(cls, symbol) -> pd.DataFrame:
        """Xem stock_shareholder.shareholders_relationship. / See stock_shareholder.shareholders_relationship."""
        return stock_shareholder(symbol).shareholders_relationship()

    @classmethod
    def get_insider_trans(cls, symbol) -> pd.DataFrame:
        """Xem stock_shareholder.insider_trans. / See stock_shareholder.insider_trans."""
        return stock_shareholder(symbol).insider_trans()

    # ===== EVENT =====
    @classmethod
    def get_news(cls, symbol) -> pd.DataFrame:
        """Xem stock_event.news. / See stock_event.news."""
        return stock_event(symbol).news()

    @classmethod
    def get_dividend(cls, symbol, start=None, end=None) -> pd.DataFrame:
        """Xem stock_event.dividend. / See stock_event.dividend."""
        return stock_event(symbol).dividend(start, end)

    @classmethod
    def get_general_meeting(cls, symbol, start=None, end=None) -> pd.DataFrame:
        """Xem stock_event.general_meeting. / See stock_event.general_meeting."""
        return stock_event(symbol).general_meeting(start, end)

    @classmethod
    def get_other_event(cls, symbol, start=None, end=None) -> pd.DataFrame:
        """Xem stock_event.other_event. / See stock_event.other_event."""
        return stock_event(symbol).other_event(start, end)


class market:
    """Dữ liệu toàn thị trường (không cần mã), gọi qua market.get_xxx(...). / Market-wide data, no symbol needed."""

    @classmethod
    def get_price_board(cls, symbols) -> pd.DataFrame:
        """Xem stock_market.price_board. / See stock_market.price_board."""
        return stock_market.price_board(symbols)

    @classmethod
    def get_event_calendar(cls, start, end, event_codes=None) -> pd.DataFrame:
        """Xem stock_event.calendar. / See stock_event.calendar."""
        return stock_event.calendar(start, end, event_codes)


class indice:
    """Chỉ số chứng khoán Việt Nam, gọi qua indice.get_xxx(...). / Vietnamese stock-market indices."""

    @classmethod
    def get_market(cls, indice: str, start: str, end: str) -> pd.DataFrame:
        """Xem indice.market. / See indice.market."""
        return _indice(indice).market(start, end)


class fund:
    """Chứng chỉ quỹ, gọi qua fund.get_xxx(...). / Fund certificates."""

    @classmethod
    def get_listing(cls) -> pd.DataFrame:
        """Xem fund.get_listing. / See fund.get_listing."""
        return _fund.get_listing()

    @classmethod
    def get_nav_history(
        cls,
        fund: Union[int, str],
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """Xem fund.nav_history. / See fund.nav_history."""
        return _fund(fund).nav_history(start, end)

    @classmethod
    def get_top_holding(cls, fund: Union[int, str]) -> pd.DataFrame:
        """Xem fund.top_holding. / See fund.top_holding."""
        return _fund(fund).top_holding()

    @classmethod
    def get_asset_holding(cls, fund: Union[int, str]) -> pd.DataFrame:
        """Xem fund.asset_holding. / See fund.asset_holding."""
        return _fund(fund).asset_holding()

    @classmethod
    def get_industries_holding(cls, fund: Union[int, str]) -> pd.DataFrame:
        """Xem fund.industries_holding. / See fund.industries_holding."""
        return _fund(fund).industries_holding()


class macro_economic:
    """Chỉ số kinh tế vĩ mô Việt Nam, gọi qua macro_economic.get_xxx(...). / Vietnam macro indicators."""

    @classmethod
    def get_general(
        cls,
        indicator: Union[int, str],
        interval: Union[int, str],
        start: Union[int, str],
        end: Union[int, str],
    ) -> pd.DataFrame:
        """Xem macro_economic.general. / See macro_economic.general."""
        return _macro_economic(indicator).general(interval, start, end)


class commodity:
    """Giá hàng hóa quốc tế, gọi qua commodity.get_xxx(). / International commodity prices."""

    @classmethod
    def get_index(cls) -> pd.DataFrame:
        """Xem commodity.get_index. / See commodity.get_index."""
        return _commodity.get_index()


class global_exchange:
    """Chỉ số chứng khoán quốc tế, gọi qua global_exchange.get_xxx(). / Global stock-market indices."""

    @classmethod
    def get_index(cls) -> pd.DataFrame:
        """Xem global_exchange.get_index. / See global_exchange.get_index."""
        return _global_exchange.get_index()


class exchange_rate:
    """Tỷ giá ngoại tệ, gọi qua exchange_rate.get_xxx(...). / Foreign-exchange rates."""

    @classmethod
    def get_vcb(cls, date=None) -> pd.DataFrame:
        """Xem vcb_exchange_rate.rates. / See vcb_exchange_rate.rates."""
        return vcb_exchange_rate.rates(date)


class gold:
    """Giá vàng, bạc trong nước, gọi qua gold.get_xxx(...). / Domestic gold and silver prices."""

    @classmethod
    def get_sjc(cls, date=None) -> pd.DataFrame:
        """Xem sjc_gold.prices. / See sjc_gold.prices."""
        return sjc_gold.prices(date)

    @classmethod
    def get_btmc(cls) -> pd.DataFrame:
        """Xem btmc_gold.prices. / See btmc_gold.prices."""
        return btmc_gold.prices()
