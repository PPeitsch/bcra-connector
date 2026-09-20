"""
BCRA API client implementation for accessing financial data from Argentina's Central Bank.
Provides interfaces for variables, checks, and currency exchange rate data endpoints.
Handles rate limiting, retries, and error cases.
"""

import logging
import math
import os
import statistics
import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

import requests

from ._http import _redact  # noqa: F401  (re-exported: used by the tests)
from ._http import HttpClient, TransportConfig
from .central_deudores import ChequesRechazados, Deudor
from .cheques import Cheque, Entidad
from .clients import (
    CambiariasClient,
    ChequesClient,
    DeudoresClient,
    MonetariasClient,
)
from .estadisticas_cambiarias import CotizacionFecha, Divisa
from .exceptions import (  # noqa: F401  (re-exported for backwards compatibility)
    BCRAApiError,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from .models import DateLike
from .principales_variables import (
    DatosVariableResponse,
    DetalleMonetaria,
    Metadata,
    PrincipalesVariables,
    Resultset,
)
from .rate_limiter import RateLimitConfig, RateLimiter
from .timeout_config import TimeoutConfig

T = TypeVar("T")


def _deprecated(old: str, new: str) -> None:
    """Warn that ``BCRAConnector.<old>()`` moved to ``connector.<new>()``."""
    warnings.warn(
        f"BCRAConnector.{old}() is deprecated and will be removed in 1.0; "
        f"use connector.{new}() instead.",
        DeprecationWarning,
        stacklevel=3,
    )


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

    # Principales Variables / Monetarias methods (v4.0)
    def get_principales_variables(self) -> List[PrincipalesVariables]:
        """Deprecated alias of :meth:`MonetariasClient.list`.

        .. deprecated:: 0.13.0
           Use ``connector.monetarias.list()``; removed in 1.0.
        """
        _deprecated("get_principales_variables", "monetarias.list")
        return self.monetarias.list().results

    def get_datos_variable(
        self,
        id_variable: int,
        desde: Optional[DateLike] = None,
        hasta: Optional[DateLike] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> DatosVariableResponse:
        """Deprecated alias of :meth:`MonetariasClient.series`.

        .. deprecated:: 0.13.0
           Use ``connector.monetarias.series()``; removed in 1.0.
        """
        _deprecated("get_datos_variable", "monetarias.series")
        page = self.monetarias.series(id_variable, desde, hasta, limit, offset)
        return DatosVariableResponse(
            status=200,
            metadata=Metadata(
                resultset=Resultset(
                    count=page.count if page.count is not None else len(page),
                    offset=page.offset,
                    limit=page.limit if page.limit is not None else len(page),
                )
            ),
            results=page.results,
        )

    def get_latest_value(self, id_variable: int) -> "DetalleMonetaria":
        """Deprecated alias of :meth:`MonetariasClient.latest`.

        .. deprecated:: 0.13.0
           Use ``connector.monetarias.latest()``; removed in 1.0.
        """
        _deprecated("get_latest_value", "monetarias.latest")
        return self.monetarias.latest(id_variable)

    # Cheques methods
    def get_entidades(self) -> List[Entidad]:
        """Deprecated alias of :meth:`ChequesClient.entities`.

        .. deprecated:: 0.13.0
           Use ``connector.cheques.entities()``; removed in 1.0.
        """
        _deprecated("get_entidades", "cheques.entities")
        return self.cheques.entities().results

    def get_cheque_denunciado(self, codigo_entidad: int, numero_cheque: int) -> Cheque:
        """Deprecated alias of :meth:`ChequesClient.reported`.

        .. deprecated:: 0.13.0
           Use ``connector.cheques.reported()``; removed in 1.0.
        """
        _deprecated("get_cheque_denunciado", "cheques.reported")
        return self.cheques.reported(codigo_entidad, numero_cheque)

    # Estadísticas Cambiarias methods
    def get_divisas(self) -> List[Divisa]:
        """Deprecated alias of :meth:`CambiariasClient.currencies`.

        .. deprecated:: 0.13.0
           Use ``connector.cambiarias.currencies()``; removed in 1.0.
        """
        _deprecated("get_divisas", "cambiarias.currencies")
        return self.cambiarias.currencies().results

    def get_cotizaciones(self, fecha: Optional[DateLike] = None) -> CotizacionFecha:
        """Deprecated alias of :meth:`CambiariasClient.quotations`.

        .. deprecated:: 0.13.0
           Use ``connector.cambiarias.quotations()``; removed in 1.0.
        """
        _deprecated("get_cotizaciones", "cambiarias.quotations")
        return self.cambiarias.quotations(fecha)

    def get_evolucion_moneda(
        self,
        moneda: str,
        fecha_desde: Optional[DateLike] = None,
        fecha_hasta: Optional[DateLike] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[CotizacionFecha]:
        """Deprecated alias of :meth:`CambiariasClient.series`.

        .. deprecated:: 0.13.0
           Use ``connector.cambiarias.series()``; removed in 1.0.
        """
        _deprecated("get_evolucion_moneda", "cambiarias.series")
        return self.cambiarias.series(
            moneda, fecha_desde, fecha_hasta, limit, offset
        ).results

    # --- Helper Methods ---
    def get_variable_by_name(
        self, variable_name: str
    ) -> Optional[PrincipalesVariables]:
        """Deprecated alias of :meth:`MonetariasClient.find`.

        .. deprecated:: 0.13.0
           Use ``connector.monetarias.find()``; removed in 1.0.
        """
        _deprecated("get_variable_by_name", "monetarias.find")
        return self.monetarias.find(variable_name)

    def get_variable_history(
        self,
        variable_name: str,
        days: int = 30,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List["DetalleMonetaria"]:
        """Deprecated alias of :meth:`MonetariasClient.history`.

        .. deprecated:: 0.13.0
           Use ``connector.monetarias.history()``; removed in 1.0.
        """
        _deprecated("get_variable_history", "monetarias.history")
        return self.monetarias.history(variable_name, days, limit, offset).results

    def get_currency_evolution(
        self,
        currency_code: str,
        days: int = 30,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[CotizacionFecha]:
        """Deprecated alias of :meth:`CambiariasClient.evolution`.

        .. deprecated:: 0.13.0
           Use ``connector.cambiarias.evolution()``; removed in 1.0.
        """
        _deprecated("get_currency_evolution", "cambiarias.evolution")
        return self.cambiarias.evolution(currency_code, days, limit, offset).results

    def check_denunciado(self, entity_name: str, check_number: int) -> bool:
        """Deprecated alias of :meth:`ChequesClient.is_reported`.

        .. deprecated:: 0.13.0
           Use ``connector.cheques.is_reported()``; removed in 1.0.
        """
        _deprecated("check_denunciado", "cheques.is_reported")
        return self.cheques.is_reported(entity_name, check_number)

    def get_latest_quotations(self) -> Dict[str, float]:
        """Deprecated alias of :meth:`CambiariasClient.latest`.

        .. deprecated:: 0.13.0
           Use ``connector.cambiarias.latest()``; removed in 1.0.
        """
        _deprecated("get_latest_quotations", "cambiarias.latest")
        return self.cambiarias.latest()

    def get_currency_pair_evolution(
        self, base_currency: str, quote_currency: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Deprecated alias of :meth:`CambiariasClient.pair`.

        .. deprecated:: 0.13.0
           Use ``connector.cambiarias.pair()``; removed in 1.0.
        """
        _deprecated("get_currency_pair_evolution", "cambiarias.pair")
        return self.cambiarias.pair(base_currency, quote_currency, days)

    def get_variable_correlation(
        self, variable_name1: str, variable_name2: str, days: int = 30
    ) -> float:
        """
        Calculate Pearson correlation between two variables/series over last n days (Monetarias v4.0).

        Handles missing data by linear interpolation. Requires numpy
        (``pip install "bcra-connector[analytics]"``).

        :param variable_name1: Name of the first variable/series.
        :param variable_name2: Name of the second variable/series.
        :param days: Number of days to look back (must be > 1).
        :return: Correlation coefficient (-1 to 1), or NaN if not calculable.
        :raises ValueError: If variables not found or days invalid.
        :raises BCRAApiError: If underlying API calls fail.
        :raises ImportError: If numpy is not installed.
        """
        if days <= 1:
            raise ValueError("Number of days must be greater than 1 for correlation.")
        try:
            import numpy as np
        except ImportError as e:
            raise ImportError(
                "get_variable_correlation() requires numpy. Install it with: "
                'pip install "bcra-connector[analytics]"'
            ) from e
        try:
            data1 = self.monetarias.history(variable_name1, days)
            data2 = self.monetarias.history(variable_name2, days)
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get history for correlation between '{variable_name1}' and '{variable_name2}': {e}"
            )
            raise

        if not data1 or not data2:
            self.logger.warning(
                f"Insufficient data for correlation: '{variable_name1}' ({len(data1)} pts), '{variable_name2}' ({len(data2)} pts)"
            )
            return math.nan

        dates1 = [d.fecha for d in data1]
        dates2 = [d.fecha for d in data2]
        values1 = np.array([d.valor for d in data1], dtype=float)
        values2 = np.array([d.valor for d in data2], dtype=float)

        if (
            len(set(dates1)) < 2 or len(set(dates2)) < 2
        ):  # Need at least two distinct time points
            self.logger.warning(
                f"Insufficient unique dates for meaningful correlation between '{variable_name1}' and '{variable_name2}'"
            )
            return math.nan

        all_dates_ord = np.array(
            sorted(list(set(d.toordinal() for d in dates1 + dates2))), dtype=float
        )
        dates1_ord = np.array([d.toordinal() for d in dates1], dtype=float)
        dates2_ord = np.array([d.toordinal() for d in dates2], dtype=float)

        # Sort data before interpolation as np.interp requires x-coordinates to be increasing
        sort_idx1 = np.argsort(dates1_ord)
        sort_idx2 = np.argsort(dates2_ord)
        interp_values1 = np.interp(
            all_dates_ord, dates1_ord[sort_idx1], values1[sort_idx1]
        )
        interp_values2 = np.interp(
            all_dates_ord, dates2_ord[sort_idx2], values2[sort_idx2]
        )

        # Check for constant series after interpolation, which makes correlation undefined or NaN
        if np.allclose(interp_values1, interp_values1[0]) or np.allclose(
            interp_values2, interp_values2[0]
        ):
            self.logger.warning(
                f"One or both series ('{variable_name1}', '{variable_name2}') are constant after interpolation. Correlation is undefined."
            )
            return math.nan
        correlation = float(np.corrcoef(interp_values1, interp_values2)[0, 1])

        if math.isnan(correlation):
            self.logger.warning(
                f"Correlation calculation resulted in NaN for '{variable_name1}' and '{variable_name2}'. Check data variability."
            )
            # This can happen if variance is zero for one of the series after interpolation
        else:
            self.logger.info(
                f"Correlation between '{variable_name1}' and '{variable_name2}' ({days} days): {correlation:.4f}"
            )
        return correlation

    def generate_variable_report(
        self, variable_name: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a given variable/series (Monetarias v4.0).

        :param variable_name: The name of the variable/series.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :return: A dictionary containing various statistics and information.
        :raises ValueError: If the variable is not found or days is invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        variable = self.monetarias.find(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")
        try:
            data = self.monetarias.history(variable_name, days)
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get history for report on '{variable_name}': {e}"
            )
            raise

        report_base = {
            "variable_name": variable_name,
            "variable_id": variable.id_variable,
            "description": variable.descripcion,
            "category": getattr(
                variable, "categoria", "N/A"
            ),  # Uses updated PrincipalesVariables model
            "period": f"Last {days} days",
        }
        if not data:
            self.logger.warning(
                f"No data available for report on '{variable_name}' for the last {days} days."
            )
            return {
                **report_base,
                "error": "No data available for the specified period",
            }

        # The API returns series newest-first; the statistics below assume the
        # data runs from oldest to newest.
        rows = sorted(data, key=lambda d: d.fecha)
        values = [float(d.valor) for d in rows]
        dates = [d.fecha for d in rows]

        # Calculate statistics, handling cases where values might be empty.
        # std_dev is the population standard deviation.
        mean_val = statistics.fmean(values) if values else None
        median_val = float(statistics.median(values)) if values else None
        min_val = min(values) if values else None
        max_val = max(values) if values else None
        std_dev_val = statistics.pstdev(values) if values else None
        latest_val = values[-1] if values else None
        start_val = values[0] if values else None

        percent_change_val = None
        if latest_val is not None and start_val is not None and start_val != 0:
            percent_change_val = (latest_val - start_val) / start_val * 100.0

        return {
            **report_base,
            "start_date": dates[0].isoformat() if dates else None,
            "end_date": dates[-1].isoformat() if dates else None,
            "latest_value": latest_val,
            "latest_date": dates[-1].isoformat() if dates else None,
            "min_value": min_val,
            "max_value": max_val,
            "mean_value": mean_val,
            "median_value": median_val,
            "std_dev": std_dev_val,
            "data_points": len(values),
            "percent_change": percent_change_val,
        }

    # Central de Deudores methods (v1.0)
    def get_deudas(self, identificacion: str) -> Deudor:
        """Deprecated alias of :meth:`DeudoresClient.debts`.

        .. deprecated:: 0.13.0
           Use ``connector.deudores.debts()``; removed in 1.0.
        """
        _deprecated("get_deudas", "deudores.debts")
        return self.deudores.debts(identificacion)

    def get_deudas_historicas(self, identificacion: str) -> Deudor:
        """Deprecated alias of :meth:`DeudoresClient.historical`.

        .. deprecated:: 0.13.0
           Use ``connector.deudores.historical()``; removed in 1.0.
        """
        _deprecated("get_deudas_historicas", "deudores.historical")
        return self.deudores.historical(identificacion)

    def get_cheques_rechazados(self, identificacion: str) -> ChequesRechazados:
        """Deprecated alias of :meth:`DeudoresClient.rejected_checks`.

        .. deprecated:: 0.13.0
           Use ``connector.deudores.rejected_checks()``; removed in 1.0.
        """
        _deprecated("get_cheques_rechazados", "deudores.rejected_checks")
        return self.deudores.rejected_checks(identificacion)
