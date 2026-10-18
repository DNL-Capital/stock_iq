import functools


class stockiqError(Exception):
    """Base class for every error this library raises."""


class InvalidParameterError(stockiqError, ValueError):
    """A caller-supplied argument is invalid (interval, date, symbol, ...).

    Subclasses ValueError so existing ``except ValueError`` code keeps working.
    """


class DataFetchError(stockiqError):
    """Fetching or parsing data from the source failed."""


def validate_interval(interval, allowed):
    """Raise InvalidParameterError if ``interval`` is not in ``allowed``.

    ``allowed`` is any container of valid interval keys — typically one of the
    ``TIMEFRAME_*`` maps in ``constants.py``.
    """
    if interval not in allowed:
        raise InvalidParameterError(
            f"interval={interval!r} không hợp lệ. Chọn một trong: {sorted(allowed)}"
        )


def wrap_errors(message="Lấy dữ liệu thất bại: {error}"):
    """Decorator: turn any unexpected error in a data method into DataFetchError.

    ``stockiqError`` (e.g. InvalidParameterError) passes through untouched. For
    anything else ``message`` is formatted with ``error`` (the original exception)
    and, for methods, ``self``, e.g. ``"Không lấy được dữ liệu cho '{self.symbol}': {error}"``.
    The original exception is kept as ``__cause__``.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except stockiqError:
                raise
            except Exception as e:
                owner = args[0] if args else None
                raise DataFetchError(message.format(self=owner, error=e)) from e

        return wrapper

    return decorator
