from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import DataFetchError

# Injected when a call site does not pass its own timeout.
REQUEST_TIMEOUT = 30

# Retry transient failures only: connection errors and these status codes.
# The data POSTs here are read-only queries, so retrying them is safe.
_RETRY = Retry(
    total=3,
    backoff_factor=1.0,  # waits grow exponentially: ~0s, 2s, 4s between attempts
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "POST"]),
    respect_retry_after_header=True,
)


class _Http:
    """Minimal ``requests``-compatible facade over one pooled session."""

    def __init__(self) -> None:
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=_RETRY)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._send("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._send("POST", url, **kwargs)

    def _send(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.RequestException as e:
            # A network error, a timeout, exhausted retries or a non-2xx status
            # all surface as one typed error the caller can catch deliberately.
            raise DataFetchError(f"Yêu cầu tới {url} thất bại: {e}") from e
        return response


# Shared instance used across the library.
NET = _Http()
