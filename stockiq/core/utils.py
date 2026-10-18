from datetime import datetime

import pandas as pd

from .exceptions import InvalidParameterError

_QUY = {"1": "Q1", "4": "Q2", "7": "Q3", "10": "Q4"}


def parse_date(value, name="date"):
    """Parse a 'YYYY-MM-DD' string into a datetime.

    Raises InvalidParameterError (a ValueError) naming the offending argument.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError) as e:
        raise InvalidParameterError(
            f"{name}={value!r} không hợp lệ. Dùng định dạng YYYY-MM-DD."
        ) from e


def to_day(values):
    """Date strings (optionally with a "T..." time part) to datetime, date part only.

    Unparseable or missing values become NaT.
    """
    return pd.to_datetime(values.astype(str).str.split("T").str[0], errors="coerce")


def to_yyyymmdd(value, name="date"):
    """Turn a 'YYYY-MM-DD' string into the 'YYYYMMDD' form the sources expect."""
    return parse_date(value, name).strftime("%Y%m%d")


def range_to_yyyymmdd(interval, start, end):
    """Turn (interval, start, end) into a ('YYYYMMDD', 'YYYYMMDD') pair.

    For months/quarters/years the range is first widened to whole periods, to
    match what the source expects.
    """
    if interval == "months":
        start, end = start + "-01", end + "-01"
    elif interval == "quarters":
        start, end = start + "-01-01", end + "-12-31"
    elif interval == "years":
        start, end = start + "-01-01", end + "-01-01"
    return to_yyyymmdd(start, "start"), to_yyyymmdd(end, "end")


def reformat_period(dates, interval):
    """Relabel a datetime Series to match the requested interval.

    days (or anything else) -> unchanged; months -> 'YYYY-MM';
    quarters -> 'Qn YYYY'; years -> integer year.
    """
    if interval == "months":
        return dates.dt.strftime("%Y-%m")
    if interval == "quarters":
        return (
            dates.dt.month.map(lambda m: _QUY.get(str(m), ""))
            + " "
            + dates.dt.year.astype(str)
        )
    if interval == "years":
        return dates.dt.strftime("%Y").astype(int)
    return dates
