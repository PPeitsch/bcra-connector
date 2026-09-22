"""
BCRA API client implementation for accessing financial data from Argentina's Central Bank.
Provides interfaces for variables, checks, and currency exchange rate data endpoints.
Handles rate limiting, retries, and error cases.
"""

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

import requests

from ._http import _redact  # noqa: F401  (re-exported: used by the tests)
from ._http import HttpClient, TransportConfig
from .clients import (
    CambiariasClient,
    ChequesClient,
    DeudoresClient,
    MonetariasClient,
)
from .exceptions import (  # noqa: F401  (re-exported for backwards compatibility)
    BCRAApiError,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from .rate_limiter import RateLimitConfig, RateLimiter
from .timeout_config import TimeoutConfig

T = TypeVar("T")


def _has_active_handler(logger: logging.Logger) -> bool:
    """Whether a record from ``logger`` would reach a handler other than NullHandler."""
    current: Optional[logging.Logger] = logger
    while current is not None:
        if any(not isinstance(h, logging.NullHandler) for h in current.handlers):
            return True
        if not current.propagate:
            return False
        current = current.parent
    return False


class BCRAConnector:
    """
    A connector for the BCRA (Banco Central de la República Argentina) APIs.

    This class provides methods to interact with various BCRA APIs, including
    Principales Variables (Monetarias v4.0), Cheques, and Estadísticas Cambiarias.
    """

    BASE_URL = "https://api.bcra.gob.ar"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    DEFAULT_RATE_LIMIT = RateLimitConfig(calls=10, period=1.0, _burst=20)
    DEFAULT_TIMEOUT = TimeoutConfig.default()
    # Largest page each API accepts; without an explicit limit they return 1000.
    MAX_PAGE_SIZE = 3000  # Monetarias v4.0 (catalog and series)
    FX_MAX_PAGE_SIZE = 1000  # Estadísticas Cambiarias v1.0
    MAX_PAGES = 100  # safety cap for automatic pagination
    # How long name lookups reuse the variables catalog and the cheque entities list
    # (seconds). 0 disables the cache. Public fetch methods are never cached.
    CATALOG_CACHE_TTL = 300.0

    def __init__(
        self,
        language: str = "es-AR",
        verify_ssl: Union[bool, str, "os.PathLike[str]"] = True,
        debug: bool = False,
        rate_limit: Optional[RateLimitConfig] = None,
        timeout: Optional[Union[TimeoutConfig, float]] = None,
        session: Optional[requests.Session] = None,
    ):
        """Initialize the BCRAConnector.

        :param language: The language for API responses, defaults to "es-AR"
        :param verify_ssl: Whether to verify SSL certificates, defaults to True.
                           A path to a CA bundle (e.g. a corporate proxy's CA)
                           verifies against that bundle instead, as in requests.
        :param debug: Opt-in debug logging, defaults to False. Sets the
                      ``bcra_connector`` loggers to DEBUG and, if no handler is
                      configured, adds one writing to stderr. Without it the
                      library leaves logging configuration to the application.
        :param rate_limit: Rate limiting configuration, defaults to DEFAULT_RATE_LIMIT
        :param timeout: Request timeout configuration, can be TimeoutConfig or float,
                      defaults to DEFAULT_TIMEOUT
        :param session: A ``requests.Session`` to use instead of a new one, for
                      custom adapters, proxies or tests. The caller keeps ownership:
                      ``close()`` leaves it open.
        """
        # A library must not configure logging: handlers and levels belong to the
        # application. ``debug=True`` is the only, explicit, exception.
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
            if not _has_active_handler(self.logger):
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )
                self.logger.addHandler(handler)

        if isinstance(timeout, (int, float)):
            resolved_timeout = TimeoutConfig.from_total(float(timeout))
        elif isinstance(timeout, TimeoutConfig):
            resolved_timeout = timeout
        else:
            resolved_timeout = self.DEFAULT_TIMEOUT

        self._http = HttpClient(
            logger=self.logger,
            config=self._transport_config,
            language=language,
            verify_ssl=verify_ssl,
            timeout=resolved_timeout,
            rate_limiter=RateLimiter(rate_limit or self.DEFAULT_RATE_LIMIT),
            session=session,
        )
        self.cheques = ChequesClient(self._http)
        self.monetarias = MonetariasClient(self._http)
        self.cambiarias = CambiariasClient(self._http)
        self.deudores = DeudoresClient(self._http)

    def _transport_config(self) -> TransportConfig:
        """Snapshot of the transport knobs, read by the client on every call.

        They stay class attributes so that overriding them on a subclass (the
        documented way) or on an instance keeps working. In 1.0 they become
        constructor arguments.
        """
        return TransportConfig(
            base_url=self.BASE_URL,
            max_retries=self.MAX_RETRIES,
            retry_delay=self.RETRY_DELAY,
            max_pages=self.MAX_PAGES,
            cache_ttl=self.CATALOG_CACHE_TTL,
            max_page_size=self.MAX_PAGE_SIZE,
            fx_max_page_size=self.FX_MAX_PAGE_SIZE,
        )

    # The transport owns these; the attributes stay for backwards compatibility.
    @property
    def session(self) -> requests.Session:
        """The underlying ``requests`` session."""
        return self._http.session

    @session.setter
    def session(self, value: requests.Session) -> None:
        self._http.session = value

    @property
    def verify_ssl(self) -> Union[bool, str]:
        """Whether (or against which CA bundle) certificates are verified."""
        return self._http.verify_ssl

    @property
    def timeout(self) -> TimeoutConfig:
        """Connect/read timeouts used for every request."""
        return self._http.timeout

    @property
    def rate_limiter(self) -> RateLimiter:
        """The client-side rate limiter."""
        return self._http.rate_limiter

    def close(self) -> None:
        """Close the HTTP session and its pooled connections.

        A session passed in by the caller is left open: whoever created it closes it.
        """
        self._http.close()

    def __enter__(self) -> "BCRAConnector":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the BCRA API with retry logic and rate limiting."""
        return self._http.request(endpoint, params)

    def clear_cache(self) -> None:
        """Drop the cached catalogs so the next name lookup fetches them again."""
        self._http.clear_cache()

    def _cached(self, key: str, loader: Callable[[], T]) -> T:
        """Return ``loader()``, reusing its last result for ``CATALOG_CACHE_TTL``."""
        return self._http.cached(key, loader)

    def _collect_pages(
        self,
        fetch_page: Callable[[int, int], Tuple[List[T], Optional[int]]],
        page_size: int,
        what: str,
        start: int = 0,
    ) -> List[T]:
        """Fetch consecutive pages until the results are exhausted."""
        return self._http.collect_pages(fetch_page, page_size, what, start)
