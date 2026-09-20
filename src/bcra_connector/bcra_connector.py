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
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

import requests

from ._http import _redact  # noqa: F401  (re-exported: used by the tests)
from ._http import HttpClient, TransportConfig
from .central_deudores import ChequesRechazados, Deudor
from .cheques import Cheque, Entidad
from .clients import ChequesClient, DeudoresClient, MonetariasClient
from .estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha, Divisa
from .exceptions import (  # noqa: F401  (re-exported for backwards compatibility)
    BCRAApiError,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from .principales_variables import (
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
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
        return self.monetarias.list()

    def get_datos_variable(
        self,
        id_variable: int,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> DatosVariableResponse:
        """Deprecated alias of :meth:`MonetariasClient.series`.

        .. deprecated:: 0.13.0
           Use ``connector.monetarias.series()``; removed in 1.0.
        """
        _deprecated("get_datos_variable", "monetarias.series")
        return self.monetarias.series(id_variable, desde, hasta, limit, offset)

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
        return self.cheques.entities()

    def get_cheque_denunciado(self, codigo_entidad: int, numero_cheque: int) -> Cheque:
        """Deprecated alias of :meth:`ChequesClient.reported`.

        .. deprecated:: 0.13.0
           Use ``connector.cheques.reported()``; removed in 1.0.
        """
        _deprecated("get_cheque_denunciado", "cheques.reported")
        return self.cheques.reported(codigo_entidad, numero_cheque)

    # Estadísticas Cambiarias methods
    def get_divisas(self) -> List[Divisa]:
        """
        Fetch the list of all currencies.

        :return: A list of Divisa objects
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info("Fetching currencies")
        try:
            data = self._make_request("estadisticascambiarias/v1.0/Maestros/Divisas")
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError(
                    "Invalid response format for currencies: 'results' key missing or not a list."
                )
            divisas = [Divisa.from_dict(d) for d in data["results"]]
            self.logger.info(f"Successfully fetched {len(divisas)} currencies")
            return divisas
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for divisas: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error fetching currencies: {e}")
            raise BCRAApiError(f"Error fetching currencies: {str(e)}") from e

    def get_cotizaciones(self, fecha: Optional[str] = None) -> CotizacionFecha:
        """
        Fetch currency quotations for a specific date.

        :param fecha: The date for which to fetch quotations (format: YYYY-MM-DD), defaults to None (latest date)
        :return: A CotizacionFecha object with the quotations
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info(
            f"Fetching quotations for date: {fecha if fecha else 'latest'}"
        )
        try:
            params = {"fecha": fecha} if fecha else None
            data = self._make_request(
                "estadisticascambiarias/v1.0/Cotizaciones", params
            )
            if "results" not in data or not isinstance(data["results"], dict):
                raise BCRAApiError(
                    "Invalid response format for quotations: 'results' key missing or not a dict."
                )
            cotizacion = CotizacionFecha.from_dict(data["results"])
            fecha_log = (
                cotizacion.fecha.isoformat() if cotizacion.fecha else "latest available"
            )
            self.logger.info(f"Successfully fetched quotations for {fecha_log}")
            return cotizacion
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for cotizaciones: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error fetching cotizaciones for {fecha}: {e}"
            )
            raise BCRAApiError(
                f"Error fetching quotations for date {fecha}: {str(e)}"
            ) from e

    def get_evolucion_moneda(
        self,
        moneda: str,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[CotizacionFecha]:
        """
        Fetch the evolution of a specific currency's quotation.

        :param moneda: The currency code (case-sensitive in URL path).
        :param fecha_desde: Start date (format: YYYY-MM-DD), defaults to None.
        :param fecha_hasta: End date (format: YYYY-MM-DD), defaults to None.
        :param limit: Maximum number of results to return (10-1000), defaults to 1000.
        :param offset: Number of results to skip, defaults to 0.
        :return: A list of CotizacionFecha objects with the currency's evolution data.
        :raises BCRAApiError: If the API request fails or returns unexpected data.
        :raises ValueError: If the limit is out of range or offset is negative.
        """
        self.logger.info(f"Fetching evolution for currency: {moneda}")
        if not (10 <= limit <= 1000):
            raise ValueError("Limit must be between 10 and 1000 for 'evolucion_moneda'")
        if offset < 0:
            raise ValueError("Offset must be non-negative for 'evolucion_moneda'")

        evolucion, total = self._fetch_evolucion_moneda_page(
            moneda, fecha_desde, fecha_hasta, limit, offset
        )
        if total is not None and offset + len(evolucion) < total:
            self.logger.warning(
                f"Returned {len(evolucion)} of {total} quotations for {moneda} "
                f"(offset {offset}). Page with limit/offset, or use "
                f"get_currency_evolution() to fetch the whole range."
            )
        return evolucion

    def _fetch_evolucion_moneda_page(
        self,
        moneda: str,
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[CotizacionFecha], Optional[int]]:
        """Fetch one page of a currency's evolution and the total result count."""
        params = {
            k: v
            for k, v in {
                "fechaDesde": fecha_desde,
                "fechaHasta": fecha_hasta,
                "limit": limit,
                "offset": offset,
            }.items()
            if v is not None
        }

        endpoint = f"estadisticascambiarias/v1.0/Cotizaciones/{moneda}"
        try:
            data = self._make_request(endpoint, params=params if params else None)
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError(
                    f"Invalid response format for currency evolution ({moneda}): 'results' key missing/invalid."
                )
            evolucion = [CotizacionFecha.from_dict(cf) for cf in data["results"]]
            self.logger.info(
                f"Successfully fetched {len(evolucion)} data points for {moneda}"
            )
            metadata = data.get("metadata")
            count = (
                metadata.get("resultset", {}).get("count")
                if isinstance(metadata, dict)
                else None
            )
            return evolucion, count if isinstance(count, int) else None
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for {moneda} evolution: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error fetching evolution for {moneda}: {e}"
            )
            raise BCRAApiError(
                f"Error fetching evolution for {moneda}: {str(e)}"
            ) from e

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
        return self.monetarias.history(variable_name, days, limit, offset)

    def get_currency_evolution(
        self,
        currency_code: str,
        days: int = 30,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[CotizacionFecha]:
        """
        Get the evolution of a currency's quotation for the last n days.

        :param currency_code: The currency code (e.g., 'USD', 'EUR'). Case-sensitive for URL.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :param limit: Maximum number of results (10-1000). By default (None) the whole
                      range is returned, fetching as many pages as needed.
        :param offset: Number of results to skip, defaults to 0.
        :return: A list of CotizacionFecha objects.
        :raises ValueError: If days/limit/offset are invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        fecha_desde = start_date.strftime("%Y-%m-%d")
        fecha_hasta = end_date.strftime("%Y-%m-%d")

        if limit is None:
            if offset < 0:
                raise ValueError("Offset must be non-negative.")

            def fetch_page(
                page_limit: int, page_offset: int
            ) -> Tuple[List[CotizacionFecha], Optional[int]]:
                return self._fetch_evolucion_moneda_page(
                    currency_code, fecha_desde, fecha_hasta, page_limit, page_offset
                )

            return self._collect_pages(
                fetch_page,
                self.FX_MAX_PAGE_SIZE,
                f"{currency_code} quotations",
                start=offset,
            )

        return self.get_evolucion_moneda(
            currency_code,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=limit,
            offset=offset,
        )

    def check_denunciado(self, entity_name: str, check_number: int) -> bool:
        """Deprecated alias of :meth:`ChequesClient.is_reported`.

        .. deprecated:: 0.13.0
           Use ``connector.cheques.is_reported()``; removed in 1.0.
        """
        _deprecated("check_denunciado", "cheques.is_reported")
        return self.cheques.is_reported(entity_name, check_number)

    def get_latest_quotations(self) -> Dict[str, float]:
        """
        Get the latest quotations (tipo_cotizacion) for all currencies.

        :return: A dictionary with currency codes as keys and their latest quotations as values.
        :raises BCRAApiError: If fetching quotations fails.
        """
        try:
            cotizaciones = self.get_cotizaciones()
        except BCRAApiError as e:
            self.logger.error(f"Failed to get latest quotations: {e}")
            raise
        if not cotizaciones or not cotizaciones.detalle:
            self.logger.warning(
                "No quotation details found in the latest API response for quotations."
            )
            return {}
        return {
            detail.codigo_moneda: detail.tipo_cotizacion
            for detail in cotizaciones.detalle
            if detail.codigo_moneda
        }

    def get_currency_pair_evolution(
        self, base_currency: str, quote_currency: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get the evolution of a currency pair exchange rate for the last n days.

        ``tasa`` follows the usual ``BASE/QUOTE`` convention: the amount of
        ``quote_currency`` for one unit of ``base_currency`` (``USD/ARS`` ~ 1500
        pesos per dollar, ``EUR/USD`` ~ 1.15 dollars per euro).

        Both currencies are expressed in US dollars on each date: ``USD`` is 1,
        ``ARS`` is ``1 / tipoCotizacion`` of USD, and any other currency is its
        ``tipoPase`` (dollars per unit). Only the series needed are requested, so a
        pair against USD makes one request. Dates where a currency has no usable
        rate (e.g. ``REF``, which has no ``tipoPase``) are skipped with a warning.

        :param base_currency: The base currency code (e.g., 'USD'). Case-insensitive.
        :param quote_currency: The quote currency code (e.g., 'ARS'). Case-insensitive.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :return: List of dictionaries with 'fecha' (ISO format) and 'tasa' (exchange
            rate), oldest first.
        :raises ValueError: If days is invalid.
        :raises BCRAApiError: If underlying API calls fail.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        base_currency = base_currency.upper()
        quote_currency = quote_currency.upper()
        pair = f"{base_currency}/{quote_currency}"

        # Series each currency needs: USD needs none, ARS needs USD's quotation.
        sources = {"USD": None, "ARS": "USD"}
        needed: List[str] = []
        for code in (base_currency, quote_currency):
            source = sources.get(code, code)
            if source and source not in needed:
                needed.append(source)
        if not needed:  # USD/USD: fetch USD just for its dates
            needed.append("USD")

        series: Dict[str, Dict[date, CotizacionDetalle]] = {}
        try:
            for code in needed:
                by_date: Dict[date, CotizacionDetalle] = {}
                for cf in self.get_currency_evolution(code, days):
                    if not cf.fecha:
                        continue
                    try:
                        by_date[cf.fecha] = self._get_cotizacion_detalle(cf, code)
                    except ValueError:
                        self.logger.debug(
                            f"{code} not in cotizacion for {cf.fecha.isoformat()}"
                        )
                series[code] = by_date
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get evolution for currency pair {pair} due to API error: {e}"
            )
            raise

        def usd_per_unit(code: str, day: date) -> float:
            if code == "USD":
                return 1.0
            if code == "ARS":
                ars_per_usd = series["USD"][day].tipo_cotizacion
                return 1.0 / ars_per_usd if ars_per_usd else 0.0
            return series[code][day].tipo_pase

        common_dates = sorted(set.intersection(*(set(s) for s in series.values())))
        pair_evolution = []
        for day in common_dates:
            base_usd = usd_per_unit(base_currency, day)
            quote_usd = usd_per_unit(quote_currency, day)
            if base_usd > 0 and quote_usd > 0:
                pair_evolution.append(
                    {"fecha": day.isoformat(), "tasa": base_usd / quote_usd}
                )
            else:
                self.logger.warning(
                    f"No USD rate for {base_currency if base_usd <= 0 else quote_currency} "
                    f"on {day.isoformat()}, skipping {pair}."
                )
        self.logger.info(
            f"Calculated {len(pair_evolution)} data points for {pair} pair evolution."
        )
        return pair_evolution

    @staticmethod
    def _get_cotizacion_detalle(
        cotizacion_fecha: CotizacionFecha, currency_code: str
    ) -> CotizacionDetalle:
        """Helper method to get CotizacionDetalle for a specific currency from CotizacionFecha."""
        if not cotizacion_fecha or not cotizacion_fecha.detalle:
            raise ValueError(
                f"Invalid or empty CotizacionFecha object provided for currency {currency_code}."
            )
        for detail in cotizacion_fecha.detalle:
            if detail.codigo_moneda == currency_code:
                return detail
        raise ValueError(
            f"Currency {currency_code} not found in cotizacion for date {cotizacion_fecha.fecha.isoformat() if cotizacion_fecha.fecha else 'N/A'}"
        )

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
            "variable_id": variable.idVariable,
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
        data = sorted(data, key=lambda d: d.fecha)
        values = [float(d.valor) for d in data]
        dates = [d.fecha for d in data]

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
