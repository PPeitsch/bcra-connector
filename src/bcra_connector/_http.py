"""Internal HTTP transport for the BCRA APIs.

Owns the ``requests`` session, retries, rate limiting, timeouts, pagination and the
catalog cache. It is internal: applications use :class:`~bcra_connector.BCRAConnector`.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

import requests
import urllib3  # For urllib3.disable_warnings

from .__about__ import __version__
from .exceptions import (
    BCRAApiError,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from .rate_limiter import RateLimiter
from .timeout_config import TimeoutConfig

T = TypeVar("T")

# CUIT/CUIL/CDI are 11-digit identifiers (personal data under Ley 25.326).
_IDENTIFICACION_RE = re.compile(r"(?<!\d)(\d{2})\d{8}(\d)(?!\d)")


def _redact(text: str) -> str:
    """Mask 11-digit identifiers (CUIT/CUIL/CDI) so they don't reach the logs."""
    return _IDENTIFICACION_RE.sub(r"\1********\2", text)


@dataclass(frozen=True)
class TransportConfig:
    """Knobs the transport reads on every call.

    ``BCRAConnector`` rebuilds this from its class attributes, so overriding them on a
    subclass or on an instance keeps working. In 1.0 they become constructor arguments.
    """

    base_url: str = "https://api.bcra.gob.ar"
    max_retries: int = 3
    retry_delay: float = 1
    max_pages: int = 100
    cache_ttl: float = 300.0


class HttpClient:
    """Talks to the BCRA APIs: one request method, pagination and a small cache."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        config: Callable[[], TransportConfig],
        language: str = "es-AR",
        verify_ssl: Union[bool, str, "os.PathLike[str]"] = True,
        timeout: Optional[TimeoutConfig] = None,
        rate_limiter: RateLimiter,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.logger = logger
        self._config = config
        self.owns_session = session is None
        self.session = session if session is not None else requests.Session()
        self.session.headers.update(
            {"Accept-Language": language, "User-Agent": f"bcra-connector/{__version__}"}
        )
        self.timeout = timeout if timeout is not None else TimeoutConfig.default()
        self.rate_limiter = rate_limiter
        self.verify_ssl: Union[bool, str]
        if isinstance(verify_ssl, bool):
            self.verify_ssl = verify_ssl
        else:
            self.verify_ssl = os.fspath(verify_ssl)
            if not os.path.exists(self.verify_ssl):
                raise ValueError(f"CA bundle not found: {self.verify_ssl}")
        self._cache: Dict[str, Tuple[float, Any]] = {}

        if not self.verify_ssl:
            self.logger.warning(
                "SSL verification is disabled. This is not recommended for production use."
            )
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def close(self) -> None:
        """Close the session, unless it was injected by the caller."""
        if self.owns_session:
            self.session.close()

    def request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the BCRA API with retry logic and rate limiting."""
        config = self._config()
        url = f"{config.base_url}/{endpoint}"
        log_url = _redact(url)
        max_retries = config.max_retries

        for attempt in range(max_retries):
            try:
                delay = self.rate_limiter.acquire()
                if delay > 0:
                    self.logger.debug(
                        f"Rate limit applied. Waiting {delay:.2f} seconds"
                    )
                    time.sleep(delay)

                self.logger.debug(f"Making request to {log_url} with params {params}")
                response = self.session.get(
                    url,
                    params=params,
                    verify=self.verify_ssl,
                    timeout=self.timeout.as_tuple,
                )
                response.raise_for_status()
                return dict(response.json())

            except requests.HTTPError as e:
                status_code = e.response.status_code
                error_msg = f"HTTP {status_code} for {e.response.url}"
                try:
                    error_data = e.response.json()
                    if "errorMessages" in error_data:
                        error_msg += f": {', '.join(error_data['errorMessages'])}"
                    elif isinstance(error_data, dict):
                        error_msg += f": {str(error_data)}"
                except (ValueError, json.JSONDecodeError):
                    error_msg += f": {e.response.reason}"

                if status_code == 404:
                    raise BCRANotFoundError(
                        f"Resource not found (404): {error_msg}", status_code
                    ) from e
                # Server-side (5xx) and rate-limit (429) errors are transient: retry
                # with exponential backoff before giving up.
                if status_code == 429 or 500 <= status_code <= 599:
                    self.logger.warning(
                        f"Transient HTTP {status_code} from {log_url} "
                        f"(attempt {attempt + 1}/{max_retries}): "
                        f"{_redact(error_msg)}"
                    )
                    if attempt == max_retries - 1:
                        error_cls = (
                            BCRARateLimitError
                            if status_code == 429
                            else BCRAServerError
                        )
                        raise error_cls(
                            f"El servidor del BCRA rechazó la conexión "
                            f"(HTTP {status_code}) tras {max_retries} intentos. "
                            f"El servidor puede estar caído o sobrecargado. "
                            f"Detalle: {error_msg}",
                            status_code,
                        ) from e
                    time.sleep(config.retry_delay * (2**attempt))
                    continue
                raise BCRAApiError(error_msg, status_code) from e

            except requests.Timeout as e:
                self.logger.error(
                    f"Request timed out to {log_url} (attempt {attempt + 1}/{max_retries})"
                )
                if attempt == max_retries - 1:
                    raise BCRAApiError(
                        f"Request timed out after {max_retries} attempts to {url}"
                    ) from e
                time.sleep(config.retry_delay * (2**attempt))

            except requests.ConnectionError as e:
                if "SSL" in str(e).upper():
                    raise BCRAApiError(f"SSL issue for {url}: {e}") from e
                self.logger.warning(
                    f"Connection error to {log_url} "
                    f"(attempt {attempt + 1}/{max_retries}): {_redact(str(e))}"
                )
                if attempt == max_retries - 1:
                    raise BCRAApiError(
                        f"API request failed: Connection error to {url} after {max_retries} attempts"
                    ) from e
                time.sleep(config.retry_delay * (2**attempt))

            except requests.RequestException as e:
                self.logger.error(
                    f"API request exception for {log_url}: {_redact(str(e))} "
                    f"(attempt {attempt+1}/{max_retries})"
                )
                if attempt == max_retries - 1:
                    raise BCRAApiError(
                        f"API request failed after {max_retries} attempts: {e}"
                    ) from e
                time.sleep(config.retry_delay * (2**attempt))

            except (ValueError, json.JSONDecodeError) as e:
                raise BCRAApiError(f"Invalid JSON response from {url}") from e

        raise BCRAApiError(f"Maximum retry attempts ({max_retries}) reached for {url}")

    def clear_cache(self) -> None:
        """Drop the cached catalogs so the next name lookup fetches them again."""
        self._cache.clear()

    def cached(self, key: str, loader: Callable[[], T]) -> T:
        """Return ``loader()``, reusing its last result for ``cache_ttl`` seconds.

        Only successful results are stored: an exception propagates and the next
        call tries again.
        """
        ttl = self._config().cache_ttl
        now = time.monotonic()
        entry = self._cache.get(key)
        if entry is not None and now - entry[0] < ttl:
            return cast(T, entry[1])
        value = loader()
        if ttl > 0:
            self._cache[key] = (now, value)
        return value

    def collect_pages(
        self,
        fetch_page: Callable[[int, int], Tuple[List[T], Optional[int]]],
        page_size: int,
        what: str,
        start: int = 0,
    ) -> List[T]:
        """Fetch consecutive pages until the results are exhausted.

        ``fetch_page(limit, offset)`` returns the page items and the total number of
        results when the endpoint reports it reliably (``None`` otherwise). Paging
        stops on a short page or once the total is reached.
        """
        max_pages = self._config().max_pages
        items: List[T] = []
        for page_number in range(max_pages):
            page, total = fetch_page(page_size, start + page_number * page_size)
            items.extend(page)
            if len(page) < page_size or (
                total is not None and start + len(items) >= total
            ):
                return items
        self.logger.warning(
            f"Stopped paging {what} after {max_pages} pages "
            f"({len(items)} results); the result may be incomplete."
        )
        return items
