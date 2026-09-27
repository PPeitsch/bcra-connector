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
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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


def _retry_after(response: requests.Response) -> Optional[float]:
    """Seconds the server asked to wait (``Retry-After``), or ``None`` if unusable.

    The header is either a number of seconds or an HTTP date; a date in the past
    means "now".
    """
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


@dataclass(frozen=True)
class TransportConfig:
    """The transport knobs, fixed when the connector is constructed."""

    base_url: str = "https://api.bcra.gob.ar"
    max_retries: int = 3
    retry_delay: float = 1
    max_retry_after: float = 30.0
    max_pages: int = 100
    cache_ttl: float = 300.0
    max_page_size: int = 3000
    fx_max_page_size: int = 1000


class HttpClient:
    """Talks to the BCRA APIs: one request method, pagination and a small cache."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        config: TransportConfig,
        language: str = "es-AR",
        verify_ssl: Union[bool, str, "os.PathLike[str]"] = True,
        timeout: Optional[TimeoutConfig] = None,
        rate_limiter: RateLimiter,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.logger = logger
        self.config = config
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
        """Make a request to the BCRA API with retry logic and rate limiting.

        Every error message masks the CUIT/CUIL in the URL, and the exception is
        raised without the ``requests`` one chained to it: that one carries the
        full URL.
        """
        config = self.config
        url = f"{config.base_url}/{endpoint}"
        safe_url = _redact(url)
        max_retries = config.max_retries

        for attempt in range(max_retries):
            last_attempt = attempt == max_retries - 1
            failure: Optional[BCRAApiError] = None
            try:
                delay = self.rate_limiter.acquire()
                if delay > 0:
                    self.logger.debug(
                        f"Rate limit applied. Waiting {delay:.2f} seconds"
                    )
                    time.sleep(delay)

                self.logger.debug(f"Making request to {safe_url} with params {params}")
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
                error_msg = _redact(error_msg)

                if status_code == 404:
                    failure = BCRANotFoundError(
                        f"Resource not found (404): {error_msg}", status_code
                    )
                # Server-side (5xx) and rate-limit (429) errors are transient: retry
                # with exponential backoff before giving up.
                elif status_code == 429 or 500 <= status_code <= 599:
                    self.logger.warning(
                        f"Transient HTTP {status_code} from {safe_url} "
                        f"(attempt {attempt + 1}/{max_retries}): {error_msg}"
                    )
                    if status_code == 429:
                        # The BCRA doesn't document its limits: the headers of a 429
                        # are the only hint of what it expects.
                        headers = {
                            k: v
                            for k, v in e.response.headers.items()
                            if k.lower() != "set-cookie"
                        }
                        self.logger.warning(f"HTTP 429 response headers: {headers}")
                    if last_attempt:
                        error_cls = (
                            BCRARateLimitError
                            if status_code == 429
                            else BCRAServerError
                        )
                        failure = error_cls(
                            f"El servidor del BCRA rechazó la conexión "
                            f"(HTTP {status_code}) tras {max_retries} intentos. "
                            f"El servidor puede estar caído o sobrecargado. "
                            f"Detalle: {error_msg}",
                            status_code,
                        )
                    else:
                        delay = config.retry_delay * (2**attempt)
                        retry_after = (
                            _retry_after(e.response)
                            if status_code in (429, 503)
                            else None
                        )
                        if retry_after is not None:
                            # Honour the server, but a bad header must not hang the
                            # caller.
                            delay = min(retry_after, config.max_retry_after)
                            self.logger.debug(
                                f"Retry-After: {retry_after:.0f}s, waiting {delay:.0f}s"
                            )
                        time.sleep(delay)
                else:
                    failure = BCRAApiError(error_msg, status_code)

            except requests.Timeout:
                self.logger.error(
                    f"Request timed out to {safe_url} (attempt {attempt + 1}/{max_retries})"
                )
                if last_attempt:
                    failure = BCRAApiError(
                        f"Request timed out after {max_retries} attempts to {safe_url}"
                    )
                else:
                    time.sleep(config.retry_delay * (2**attempt))

            except requests.ConnectionError as e:
                detail = _redact(str(e))
                if "SSL" in detail.upper():
                    failure = BCRAApiError(f"SSL issue for {safe_url}: {detail}")
                else:
                    self.logger.warning(
                        f"Connection error to {safe_url} "
                        f"(attempt {attempt + 1}/{max_retries}): {detail}"
                    )
                    if last_attempt:
                        failure = BCRAApiError(
                            f"API request failed: Connection error to {safe_url} "
                            f"after {max_retries} attempts"
                        )
                    else:
                        time.sleep(config.retry_delay * (2**attempt))

            except requests.RequestException as e:
                detail = _redact(str(e))
                self.logger.error(
                    f"API request exception for {safe_url}: {detail} "
                    f"(attempt {attempt+1}/{max_retries})"
                )
                if last_attempt:
                    failure = BCRAApiError(
                        f"API request failed after {max_retries} attempts: "
                        f"{detail} ({safe_url})"
                    )
                else:
                    time.sleep(config.retry_delay * (2**attempt))

            except (ValueError, json.JSONDecodeError):
                failure = BCRAApiError(f"Invalid JSON response from {safe_url}")

            if failure is not None:
                # Raised outside the ``except`` on purpose: inside it, Python would
                # chain the ``requests`` exception as ``__context__``, and its message
                # has the unmasked URL (#169).
                raise failure

        raise BCRAApiError(
            f"Maximum retry attempts ({max_retries}) reached for {safe_url}"
        )

    def clear_cache(self) -> None:
        """Drop the cached catalogs so the next name lookup fetches them again."""
        self._cache.clear()

    def cached(self, key: str, loader: Callable[[], T]) -> T:
        """Return ``loader()``, reusing its last result for ``cache_ttl`` seconds.

        Only successful results are stored: an exception propagates and the next
        call tries again.
        """
        ttl = self.config.cache_ttl
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
        max_pages = self.config.max_pages
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
