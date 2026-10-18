from typing import Literal

# Different method groups accept different interval sets — kept separate on purpose.
IntervalOHLC = Literal["days", "months", "minutes", "hours"]  # history()
IntervalReport = Literal[
    "days", "months", "quarters", "years"
]  # price/foreign/proprietary/demand
IntervalFinancial = Literal[
    "years", "quarters"
]  # finance_ratio/balance_sheet/income_statement/cash_flow

ExchangeStr = Literal["HOSE", "HNX", "UPCOM"]
