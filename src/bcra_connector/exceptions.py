"""Exceptions raised by the BCRA connector.

Every error is a :class:`BCRAApiError`, so ``except BCRAApiError`` catches all of
them. The subclasses let callers react to specific HTTP outcomes without parsing
messages.
"""

from typing import Optional


class BCRAApiError(Exception):
    """Error calling a BCRA API or parsing its response.

    :param message: Human-readable description.
    :param status_code: HTTP status of the failed response, or ``None`` when there
        was no HTTP response (timeout, connection or SSL error, invalid JSON).
    """

    def __init__(self, message: str = "", status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BCRANotFoundError(BCRAApiError):
    """HTTP 404: the resource doesn't exist (unknown variable, CUIT, entity...)."""


class BCRARateLimitError(BCRAApiError):
    """HTTP 429 that persisted after the retries."""


class BCRAServerError(BCRAApiError):
    """HTTP 5xx that persisted after the retries."""
