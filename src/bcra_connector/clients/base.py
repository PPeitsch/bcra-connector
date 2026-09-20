"""Shared plumbing for the per-domain clients."""

from typing import Any, Callable, Dict, TypeVar

from .._http import HttpClient
from ..exceptions import BCRAApiError
from ..models import Page, resultset

T = TypeVar("T")


class DomainClient:
    """Base for the clients behind ``connector.monetarias``, ``.cheques``, ..."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self.logger = http.logger

    def _list(
        self,
        endpoint: str,
        parser: Callable[[Dict[str, Any]], T],
        what: str,
    ) -> Page[T]:
        """GET an endpoint whose ``results`` is a list, each item parsed by ``parser``."""
        try:
            data = self._http.request(endpoint)
            results = data.get("results")
            if not isinstance(results, list):
                raise BCRAApiError(
                    f"Invalid response format for {what}: "
                    "'results' key missing or not a list."
                )
            rows = [parser(item) for item in results]
            return Page(rows, **{"count": len(rows), **resultset(data)})
        except BCRAApiError:
            raise
        except (KeyError, TypeError, ValueError) as e:
            raise BCRAApiError(f"Unexpected response format for {what}: {e}") from e
        except Exception as e:
            self.logger.exception(f"Unexpected error fetching {what}: {e}")
            raise BCRAApiError(f"Error fetching {what}: {e}") from e

    def _object(
        self,
        endpoint: str,
        parser: Callable[[Dict[str, Any]], T],
        what: str,
    ) -> T:
        """GET an endpoint whose ``results`` is a single object, parsed by ``parser``.

        Replaces the try/except block that every endpoint method used to repeat:
        a parsing failure becomes a :class:`BCRAApiError` naming what was being read.
        """
        try:
            data = self._http.request(endpoint)
            results = data.get("results")
            if not isinstance(results, dict):
                raise BCRAApiError(
                    f"Invalid response format for {what}: "
                    "'results' key missing or not a dict."
                )
            return parser(results)
        except BCRAApiError:
            raise
        except (KeyError, TypeError, ValueError) as e:
            raise BCRAApiError(f"Unexpected response format for {what}: {e}") from e
        except Exception as e:
            self.logger.exception(f"Unexpected error fetching {what}: {e}")
            raise BCRAApiError(f"Error fetching {what}: {e}") from e


def identificacion(value: str) -> str:
    """Normalize and validate a CUIT/CUIL/CDI, accepting the dashed form."""
    cleaned = value.replace("-", "").replace(" ", "")
    if len(cleaned) != 11 or not cleaned.isdigit():
        raise ValueError("Identificacion must be exactly 11 digits")
    return cleaned
