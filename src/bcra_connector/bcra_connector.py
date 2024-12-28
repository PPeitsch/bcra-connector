"""
BCRA API client implementation for accessing financial data from Argentina's Central Bank.
Provides interfaces for variables, checks, and currency exchange rate data endpoints.
Handles rate limiting, retries, and error cases.
"""

import logging
import ssl
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import requests
import urllib3
from scipy.stats import pearsonr
from urllib3.exceptions import SSLError as URLLibSSLError

from .cheques import Cheque, Entidad
from .estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha, Divisa
from .principales_variables import DatosVariable, PrincipalesVariables
from .rate_limiter import RateLimitConfig, RateLimiter
from .timeout_config import TimeoutConfig


class BCRAApiError(Exception):
    """Custom exception for BCRA API errors."""

    pass


class BCRAConnector:
    """
    A connector for the BCRA (Banco Central de la República Argentina) APIs.

    This class provides methods to interact with various BCRA APIs, including
    Principales Variables, Cheques, and Estadísticas Cambiarias.
    """

    BASE_URL = "https://api.bcra.gob.ar"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    DEFAULT_RATE_LIMIT = RateLimitConfig(
        calls=10,  # 10 calls
        period=1.0,  # per second
        _burst=20,  # allowing up to 20 calls
    )
    DEFAULT_TIMEOUT = TimeoutConfig.default()

    def __init__(
        self,
        language: str = "es-AR",
        verify_ssl: bool = True,
        debug: bool = False,
        rate_limit: Optional[RateLimitConfig] = None,
        timeout: Optional[Union[TimeoutConfig, float]] = None,
    ):
        """Initialize the BCRAConnector.

        :param language: The language for API responses, defaults to "es-AR"
        :param verify_ssl: Whether to verify SSL certificates, defaults to True
        :param debug: Whether to enable debug logging, defaults to False
        :param rate_limit: Rate limiting configuration, defaults to DEFAULT_RATE_LIMIT
        :param timeout: Request timeout configuration, can be TimeoutConfig or float,
                      defaults to DEFAULT_TIMEOUT
        """
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept-Language": language, "User-Agent": "BCRAConnector/1.0"}
        )
        self.verify_ssl = verify_ssl

        # Configure timeouts
        if isinstance(timeout, (int, float)):
            self.timeout = TimeoutConfig.from_total(float(timeout))
        elif isinstance(timeout, TimeoutConfig):
            self.timeout = timeout
        else:
            self.timeout = self.DEFAULT_TIMEOUT

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(rate_limit or self.DEFAULT_RATE_LIMIT)

        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        if not self.verify_ssl:
            self.logger.warning(
                "SSL verification is disabled. This is not recommended for production use."
            )
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the BCRA API with retry logic and rate limiting."""
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                # Apply rate limiting
                delay = self.rate_limiter.acquire()
                if delay > 0:
                    self.logger.debug(
                        f"Rate limit applied. Waiting {delay:.2f} seconds"
                    )
                    time.sleep(delay)  # Actually wait instead of raising an error

                self.logger.debug(f"Making request to {url}")
                response = self.session.get(
                    url,
                    params=params,
                    verify=self.verify_ssl,
                    timeout=self.timeout.as_tuple,
                )

                try:
                    response.raise_for_status()
                except requests.HTTPError as e:
                    status_code = response.status_code
                    if status_code == 404:
                        raise BCRAApiError("HTTP 404: Resource not found") from e

                    error_msg = f"HTTP {status_code}"
                    try:
                        error_data = response.json()
                        if "errorMessages" in error_data:
                            error_msg = (
                                f"{error_msg}: {', '.join(error_data['errorMessages'])}"
                            )
                    except (ValueError, KeyError):
                        error_msg = f"{error_msg}: {response.reason}"
                    raise BCRAApiError(error_msg) from e

                try:
                    return dict(response.json())
                except ValueError as e:
                    raise BCRAApiError("Invalid JSON response") from e

            except requests.Timeout as e:
                self.logger.error(
                    f"Request timed out (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError("Request timed out") from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

            except requests.ConnectionError as e:
                if "SSL" in str(e):
                    raise BCRAApiError("SSL verification failed") from e

                self.logger.warning(
                    f"Connection error (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError("API request failed: Connection error") from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

            except requests.RequestException as e:
                raise BCRAApiError(f"API request failed: {str(e)}") from e

        raise BCRAApiError("Maximum retry attempts reached")

    # Principales Variables methods
    def get_principales_variables(self) -> List[PrincipalesVariables]:
        """
        Fetch the list of all principal variables published by BCRA.

        :return: A list of PrincipalesVariables objects
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info("Fetching principal variables")
        try:
            data = self._make_request("estadisticas/v2.0/PrincipalesVariables")

            if not isinstance(data, dict) or "results" not in data:
                raise BCRAApiError(
                    "Unexpected response format: 'results' key not found"
                )

            if not isinstance(data["results"], list):
                raise BCRAApiError(
                    "Unexpected response format: 'results' is not a list"
                )

            variables = []
            for item in data["results"]:
                try:
                    variables.append(PrincipalesVariables.from_dict(item))
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Skipping invalid variable data: {str(e)}")

            if not variables:
                self.logger.warning("No valid variables found in the response")
            else:
                self.logger.info(
                    f"Successfully fetched {len(variables)} principal variables"
                )

            return variables
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching principal variables: {str(e)}"
            self.logger.error(error_msg)
            raise BCRAApiError(error_msg) from e

    def get_datos_variable(
        self, id_variable: int, desde: datetime, hasta: datetime
    ) -> List[DatosVariable]:
        """
        Fetch the list of values for a variable within a specified date range.

        :param id_variable: The ID of the desired variable
        :param desde: The start date of the range to query
        :param hasta: The end date of the range to query
        :return: A list of DatosVariable objects
        :raises ValueError: If the date range is invalid
        :raises BCRAApiError: If the API request fails
        """
        self.logger.info(
            f"Fetching data for variable {id_variable} from {desde.date()} to {hasta.date()}"
        )

        if desde > hasta:
            raise ValueError(
                "'desde' date must be earlier than or equal to 'hasta' date"
            )

        if hasta - desde > timedelta(days=365):
            raise ValueError("Date range must not exceed 1 year")

        try:
            data = self._make_request(
                f"estadisticas/v2.0/DatosVariable/{id_variable}/{desde.date()}/{hasta.date()}"
            )
            datos = [DatosVariable.from_dict(item) for item in data["results"]]
            self.logger.info(f"Successfully fetched {len(datos)} data points")
            return datos
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

    def get_latest_value(self, id_variable: int) -> DatosVariable:
        """
        Fetch the latest value for a specific variable.

        :param id_variable: The ID of the desired variable
        :return: The latest data point for the specified variable
        :raises BCRAApiError: If the API request fails or if no data is available
        """
        self.logger.info(f"Fetching latest value for variable {id_variable}")
        end_date = datetime.now()
        start_date = end_date - timedelta(
            days=30
        )  # Look back 30 days to ensure we get data

        data = self.get_datos_variable(id_variable, start_date, end_date)
        if not data:
            raise BCRAApiError(f"No data available for variable {id_variable}")

        latest = max(data, key=lambda x: x.fecha)
        self.logger.info(
            f"Latest value for variable {id_variable}: {latest.valor} ({latest.fecha})"
        )
        return latest

    # Cheques methods
    def get_entidades(self) -> List[Entidad]:
        """
        Fetch the list of all financial entities.

        :return: A list of Entidad objects
        :raises BCRAApiError: If the API request fails
        """
        self.logger.info("Fetching financial entities")
        try:
            data = self._make_request("cheques/v1.0/entidades")
            entities = [Entidad.from_dict(e) for e in data["results"]]
            self.logger.info(f"Successfully fetched {len(entities)} entities")
            return entities
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

    def get_cheque_denunciado(self, codigo_entidad: int, numero_cheque: int) -> Cheque:
        """
        Fetch information about a reported check.

        :param codigo_entidad: The code of the financial entity
        :param numero_cheque: The check number
        :return: A Cheque object with the check's information
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info(
            f"Fetching information for check {numero_cheque} from entity {codigo_entidad}"
        )
        try:
            data = self._make_request(
                f"cheques/v1.0/denunciados/{codigo_entidad}/{numero_cheque}"
            )
            return Cheque.from_dict(data["results"])
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

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
            divisas = [Divisa(**d) for d in data["results"]]
            self.logger.info(f"Successfully fetched {len(divisas)} currencies")
            return divisas
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

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
            cotizacion = CotizacionFecha.from_dict(data["results"])
            self.logger.info(f"Successfully fetched quotations for {cotizacion.fecha}")
            return cotizacion
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

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

        :param moneda: The currency code
        :param fecha_desde: Start date (format: YYYY-MM-DD), defaults to None
        :param fecha_hasta: End date (format: YYYY-MM-DD), defaults to None
        :param limit: Maximum number of results to return (10-1000), defaults to 1000
        :param offset: Number of results to skip, defaults to 0
        :return: A list of CotizacionFecha objects with the currency's evolution data
        :raises BCRAApiError: If the API request fails or returns unexpected data
        :raises ValueError: If the limit is out of range
        """
        self.logger.info(f"Fetching evolution for currency: {moneda}")
        if limit < 10 or limit > 1000:
            raise ValueError("Limit must be between 10 and 1000")

        try:
            params = {
                "fechaDesde": fecha_desde,
                "fechaHasta": fecha_hasta,
                "limit": limit,
                "offset": offset,
            }
            params = {k: v for k, v in params.items() if v is not None}
            data = self._make_request(
                f"estadisticascambiarias/v1.0/Cotizaciones/{moneda}", params
            )
            evolucion = [CotizacionFecha.from_dict(cf) for cf in data["results"]]
            self.logger.info(
                f"Successfully fetched {len(evolucion)} data points for {moneda}"
            )
            return evolucion
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

    def get_variable_by_name(
        self, variable_name: str
    ) -> Optional[PrincipalesVariables]:
        """
        Find a principal variable by its name.

        :param variable_name: The name of the variable to find
        :return: A PrincipalesVariables object if found, None otherwise
        """
        variables = self.get_principales_variables()
        normalized_name = variable_name.lower().strip()
        for variable in variables:
            if normalized_name in variable.descripcion.lower():
                return variable
        return None

    def get_variable_history(
        self, variable_name: str, days: int = 30
    ) -> List[DatosVariable]:
        """
        Get the historical data for a variable by its name for the last n days.

        :param variable_name: The name of the variable
        :param days: The number of days to look back, defaults to 30
        :return: A list of DatosVariable objects
        :raises ValueError: If the variable is not found
        """
        variable = self.get_variable_by_name(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.get_datos_variable(variable.idVariable, start_date, end_date)

    def get_currency_evolution(
        self, currency_code: str, days: int = 30
    ) -> List[CotizacionFecha]:
        """
        Get the evolution of a currency's quotation for the last n days.

        :param currency_code: The currency code (e.g., 'USD', 'EUR')
        :param days: The number of days to look back, defaults to 30
        :return: A list of CotizacionFecha objects
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.get_evolucion_moneda(
            currency_code,
            fecha_desde=start_date.strftime("%Y-%m-%d"),
            fecha_hasta=end_date.strftime("%Y-%m-%d"),
        )

    def check_denunciado(self, entity_name: str, check_number: int) -> bool:
        """
        Check if a check is reported as stolen or lost.

        :param entity_name: The name of the financial entity
        :param check_number: The check number
        :return: True if the check is reported, False otherwise
        :raises ValueError: If the entity is not found
        """
        entities = self.get_entidades()
        entity = next(
            (e for e in entities if e.denominacion.lower() == entity_name.lower()), None
        )
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")

        cheque = self.get_cheque_denunciado(entity.codigo_entidad, check_number)
        return cheque.denunciado

    def get_latest_quotations(self) -> Dict[str, float]:
        """
        Get the latest quotations for all currencies.

        :return: A dictionary with currency codes as keys and their latest quotations as values
        """
        cotizaciones = self.get_cotizaciones()
        return {
            detail.codigo_moneda: detail.tipo_cotizacion
            for detail in cotizaciones.detalle
        }

    def get_currency_pair_evolution(
        self, base_currency: str, quote_currency: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get the evolution of a currency pair for the last n days.

        :param base_currency: The base currency code (e.g., 'USD')
        :param quote_currency: The quote currency code (e.g., 'EUR')
        :param days: The number of days to look back, defaults to 30
        :return: A list of dictionaries containing the date and the exchange rate
        """
        base_evolution = self.get_currency_evolution(base_currency, days)
        quote_evolution = self.get_currency_evolution(quote_currency, days)

        base_dict = {
            cf.fecha: self._get_cotizacion_detalle(cf, base_currency).tipo_cotizacion
            for cf in base_evolution
        }
        quote_dict = {
            cf.fecha: self._get_cotizacion_detalle(cf, quote_currency).tipo_cotizacion
            for cf in quote_evolution
        }

        pair_evolution = []
        for date in set(base_dict.keys()) & set(quote_dict.keys()):
            if base_dict[date] != 0 and date is not None:
                rate = quote_dict[date] / base_dict[date]
                pair_evolution.append({"fecha": date.isoformat(), "tasa": rate})

        return sorted(pair_evolution, key=lambda x: x["fecha"])

    @staticmethod
    def _get_cotizacion_detalle(
        cotizacion_fecha: CotizacionFecha, currency_code: str
    ) -> CotizacionDetalle:
        """
        Helper method to get CotizacionDetalle for a specific currency from CotizacionFecha.

        :param cotizacion_fecha: CotizacionFecha object
        :param currency_code: The currency code to look for
        :return: CotizacionDetalle for the specified currency
        :raises ValueError: If the currency is not found in the CotizacionFecha
        """
        for detail in cotizacion_fecha.detalle:
            if detail.codigo_moneda == currency_code:
                return detail
        raise ValueError(
            f"Currency {currency_code} not found in cotizacion for date {cotizacion_fecha.fecha}"
        )

    def get_variable_correlation(
        self, variable_name1: str, variable_name2: str, days: int = 30
    ) -> float:
        """
        Calculate the correlation between two variables over the last n days.

        :param variable_name1: The name of the first variable
        :param variable_name2: The name of the second variable
        :param days: The number of days to look back, defaults to 30
        :return: The correlation coefficient between -1 and 1
        :raises ValueError: If either variable is not found or if there's insufficient data
        """

        data1 = self.get_variable_history(variable_name1, days)
        data2 = self.get_variable_history(variable_name2, days)

        if not data1 or not data2:
            raise ValueError("Insufficient data for correlation calculation")

        dates1 = [d.fecha for d in data1]
        dates2 = [d.fecha for d in data2]
        values1 = [d.valor for d in data1]
        values2 = [d.valor for d in data2]

        # Create a date range covering both datasets
        all_dates = sorted(set(dates1 + dates2))

        # Interpolate missing values
        interp_values1 = np.interp(
            [d.toordinal() for d in all_dates], [d.toordinal() for d in dates1], values1
        )
        interp_values2 = np.interp(
            [d.toordinal() for d in all_dates], [d.toordinal() for d in dates2], values2
        )

        # Calculate correlation
        correlation, _ = pearsonr(interp_values1, interp_values2)
        return float(correlation)

    def generate_variable_report(
        self, variable_name: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a given variable.

        :param variable_name: The name of the variable
        :param days: The number of days to look back, defaults to 30
        :return: A dictionary containing various statistics and information about the variable
        :raises ValueError: If the variable is not found
        """
        variable = self.get_variable_by_name(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")

        data = self.get_variable_history(variable_name, days)

        if not data:
            return {"error": "No data available for the specified period"}

        values = [d.valor for d in data]
        dates = [d.fecha for d in data]

        report = {
            "variable_name": variable_name,
            "variable_id": variable.idVariable,
            "description": variable.descripcion,
            "period": f"Last {days} days",
            "start_date": min(dates).isoformat(),
            "end_date": max(dates).isoformat(),
            "latest_value": values[-1],
            "latest_date": dates[-1].isoformat(),
            "min_value": min(values),
            "max_value": max(values),
            "mean_value": sum(values) / len(values),
            "median_value": sorted(values)[len(values) // 2],
            "data_points": len(values),
            "percent_change": (
                (values[-1] - values[0]) / values[0] * 100 if values[0] != 0 else None
            ),
        }

        # Add 'unit' to the report only if it's available in the variable
        if hasattr(variable, "unidad"):
            report["unit"] = variable.unidad

        return report
