"""
BCRA API client implementation for accessing financial data from Argentina's Central Bank.
Provides interfaces for variables, checks, and currency exchange rate data endpoints.
Handles rate limiting, retries, and error cases.
"""

import json
import logging
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import requests
import urllib3  # For urllib3.disable_warnings
from scipy.stats import pearsonr

from .cheques import Cheque, Entidad
from .estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha, Divisa
from .principales_variables import (
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
from .rate_limiter import RateLimitConfig, RateLimiter
from .timeout_config import TimeoutConfig


class BCRAApiError(Exception):
    """Custom exception for BCRA API errors."""

    pass


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

        if isinstance(timeout, (int, float)):
            self.timeout = TimeoutConfig.from_total(float(timeout))
        elif isinstance(timeout, TimeoutConfig):
            self.timeout = timeout
        else:
            self.timeout = self.DEFAULT_TIMEOUT

        self.rate_limiter = RateLimiter(rate_limit or self.DEFAULT_RATE_LIMIT)

        log_level = logging.DEBUG if debug else logging.INFO
        # Configure logger for this instance; avoid reconfiguring root logger if already set up
        self.logger = logging.getLogger(__name__)
        if not self.logger.hasHandlers():  # Configure only if no handlers are attached
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(log_level)

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
                delay = self.rate_limiter.acquire()
                if delay > 0:
                    self.logger.debug(
                        f"Rate limit applied. Waiting {delay:.2f} seconds"
                    )
                    time.sleep(delay)

                self.logger.debug(f"Making request to {url} with params {params}")
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
                    raise BCRAApiError(f"Resource not found (404): {error_msg}") from e
                raise BCRAApiError(error_msg) from e

            except requests.Timeout as e:
                self.logger.error(
                    f"Request timed out to {url} (attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(
                        f"Request timed out after {self.MAX_RETRIES} attempts to {url}"
                    ) from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

            except requests.ConnectionError as e:
                if "SSL" in str(e).upper():
                    raise BCRAApiError(f"SSL issue for {url}: {e}") from e
                self.logger.warning(
                    f"Connection error to {url} (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(
                        f"API request failed: Connection error to {url} after {self.MAX_RETRIES} attempts"
                    ) from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

            except requests.RequestException as e:
                self.logger.error(
                    f"API request exception for {url}: {e} (attempt {attempt+1}/{self.MAX_RETRIES})"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(
                        f"API request failed after {self.MAX_RETRIES} attempts: {e}"
                    ) from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

            except (ValueError, json.JSONDecodeError) as e:
                raise BCRAApiError(f"Invalid JSON response from {url}") from e

        raise BCRAApiError(
            f"Maximum retry attempts ({self.MAX_RETRIES}) reached for {url}"
        )

    # Principales Variables / Monetarias methods (v4.0)
    def get_principales_variables(self) -> List[PrincipalesVariables]:
        """
        Fetch the list of all monetary series and principal variables published by BCRA (API v4.0).

        :return: A list of PrincipalesVariables objects with extended metadata
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info("Fetching monetary series and principal variables (v4.0)")
        try:
            data = self._make_request("estadisticas/v4.0/Monetarias")
            if not isinstance(data.get("results"), list):
                raise BCRAApiError(
                    "Unexpected response format: 'results' is not a list or missing"
                )

            variables = []
            for item in data["results"]:
                try:
                    variables.append(PrincipalesVariables.from_dict(item))
                except (ValueError, KeyError) as e:
                    self.logger.warning(
                        f"Skipping invalid variable data: {e} - Data: {item}"
                    )

            if not variables and data.get(
                "results"
            ):  # Check if results existed but parsing failed
                self.logger.error(
                    "Failed to parse any variable data despite receiving results."
                )
            elif not variables:
                self.logger.warning("No valid variables found in the response")
            else:
                self.logger.info(
                    f"Successfully fetched and parsed {len(variables)} variables (v4.0)"
                )
            return variables
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching principal variables (v4.0): {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    def get_datos_variable(
        self,
        id_variable: int,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> DatosVariableResponse:
        """
        Fetch the list of values for a variable/series (API v4.0).

        Uses pagination via limit and offset. If desde/hasta are omitted, API defaults apply.

        :param id_variable: The ID of the desired variable. Case-sensitive `{IdVariable}` in URL path.
        :param desde: The start date of the range to query (inclusive). Optional. YYYY-MM-DD format.
        :param hasta: The end date of the range to query (inclusive). Optional. YYYY-MM-DD format.
        :param limit: Maximum number of results (10-3000). Optional, API defaults to 1000.
        :param offset: Number of results to skip for pagination. Optional, defaults to 0.
        :return: A DatosVariableResponse object containing metadata and results.
        :raises ValueError: If date range is invalid or limit/offset are out of bounds.
        :raises BCRAApiError: If the API request fails.
        """
        log_msg_parts = [f"Fetching data for variable {id_variable}"]
        if desde:
            log_msg_parts.append(f"from {desde.date()}")
        if hasta:
            log_msg_parts.append(f"to {hasta.date()}")
        if limit is not None:
            log_msg_parts.append(f"limit {limit}")
        if offset is not None:
            log_msg_parts.append(f"offset {offset}")
        self.logger.info(" ".join(log_msg_parts) + " (v4.0)")

        if desde and hasta and desde > hasta:
            raise ValueError(
                "'desde' date must be earlier than or equal to 'hasta' date"
            )
        if limit is not None and not (10 <= limit <= 3000):
            raise ValueError("Limit must be between 10 and 3000")
        if offset is not None and offset < 0:
            raise ValueError("Offset must be non-negative")

        params: Dict[str, Any] = {}
        if desde:
            params["Desde"] = desde.strftime("%Y-%m-%d")
        if hasta:
            params["Hasta"] = hasta.strftime("%Y-%m-%d")
        if limit is not None:
            params["Limit"] = limit
        if offset is not None:
            params["Offset"] = offset

        endpoint = f"estadisticas/v4.0/Monetarias/{id_variable}"

        try:
            raw_api_data = self._make_request(
                endpoint, params=params if params else None
            )
            response_obj = DatosVariableResponse.from_dict(raw_api_data)
            # Count total data points across all results
            total_points = sum(len(r.detalle) for r in response_obj.results)
            self.logger.info(
                f"Successfully fetched and parsed {total_points} data points "
                f"(total available: {response_obj.metadata.resultset.count}) for variable {id_variable} (v4.0)"
            )
            return response_obj
        except (ValueError, KeyError) as e:
            error_msg = f"Error parsing response for variable {id_variable} (v4.0): {e}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e
        except BCRAApiError:
            self.logger.error(
                f"API Error fetching data for variable {id_variable} (v4.0)"
            )
            raise
        except Exception as e:
            error_msg = (
                f"Unexpected error fetching data for variable {id_variable} (v4.0): {e}"
            )
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    def get_latest_value(self, id_variable: int) -> "DetalleMonetaria":
        """
        Fetch the latest value for a specific variable using API v4.0.

        :param id_variable: The ID of the desired variable.
        :return: The latest data point (DetalleMonetaria object) for the specified variable.
        :raises BCRAApiError: If the API request fails or if no data is available.
        """
        from .principales_variables import DetalleMonetaria

        self.logger.info(
            f"Fetching latest value for variable {id_variable} (using v4.0 logic)"
        )
        response_data = self.get_datos_variable(
            id_variable, limit=10
        )  # Small limit for efficiency

        # Collect all data points from all results
        all_detalles: List[DetalleMonetaria] = []
        for result in response_data.results:
            all_detalles.extend(result.detalle)

        if not all_detalles:
            # Fallback: If no data with small limit, query last 30 days.
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            self.logger.info(
                f"No recent data found for {id_variable} with limit=10, checking last 30 days."
            )
            # Use a limit that covers roughly a month of daily data if the API allows
            effective_limit = (
                response_data.metadata.resultset.limit if response_data.metadata else 30
            )
            response_data = self.get_datos_variable(
                id_variable, desde=start_date, hasta=end_date, limit=effective_limit
            )
            # Collect all data points again
            all_detalles = []
            for result in response_data.results:
                all_detalles.extend(result.detalle)

            if not all_detalles:
                raise BCRAApiError(
                    f"No data available for variable {id_variable} in the last 30 days."
                )

        latest = max(all_detalles, key=lambda x: x.fecha)
        self.logger.info(
            f"Latest value for variable {id_variable}: {latest.valor} ({latest.fecha.isoformat()})"
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
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError(
                    "Invalid response format for entities endpoint: 'results' key missing or not a list."
                )
            entities = [Entidad.from_dict(e) for e in data["results"]]
            self.logger.info(f"Successfully fetched {len(entities)} entities")
            return entities
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for entities: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error fetching financial entities: {e}")
            raise BCRAApiError(f"Error fetching financial entities: {str(e)}") from e

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
            if "results" not in data or not isinstance(data["results"], dict):
                raise BCRAApiError(
                    "Invalid response format for reported check: 'results' key missing or not a dict."
                )
            return Cheque.from_dict(data["results"])
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for check {numero_cheque}: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error fetching check {numero_cheque}: {e}"
            )
            raise BCRAApiError(
                f"Error fetching reported check {numero_cheque}: {str(e)}"
            ) from e

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
            return evolucion
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
        """
        Find a principal variable or monetary series by its name (Uses Monetarias v3.0 API).

        :param variable_name: The name of the variable/series to find (case-insensitive search).
        :return: A PrincipalesVariables object if found, None otherwise.
        """
        try:
            variables = self.get_principales_variables()
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get variables to search by name ('{variable_name}'): {e}"
            )
            return None
        normalized_name = variable_name.lower().strip()
        for variable in variables:
            if variable.descripcion and normalized_name in variable.descripcion.lower():
                return variable
        self.logger.info(
            f"Variable/series with name containing '{variable_name}' not found."
        )
        return None

    def get_variable_history(
        self,
        variable_name: str,
        days: int = 30,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List["DetalleMonetaria"]:
        """
        Get the historical data for a variable/series by name for the last n days (Uses Monetarias v4.0 API).

        This method returns a flat list of data points for convenience.

        :param variable_name: The name of the variable/series.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :param limit: Maximum number of results (10-3000). Optional.
        :param offset: Number of results to skip for pagination. Optional.
        :return: A list of DetalleMonetaria objects.
        :raises ValueError: If the variable is not found or days/limit/offset are invalid.
        :raises BCRAApiError: If the API request fails.
        """
        from .principales_variables import DetalleMonetaria

        variable = self.get_variable_by_name(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")
        if days <= 0:
            raise ValueError("Number of days must be positive.")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        response_obj = self.get_datos_variable(
            variable.idVariable,
            desde=start_date,
            hasta=end_date,
            limit=limit,
            offset=offset,
        )
        # Flatten the results - extract all DetalleMonetaria from all DatosVariable
        all_detalles: List[DetalleMonetaria] = []
        for result in response_obj.results:
            all_detalles.extend(result.detalle)
        return all_detalles

    def get_currency_evolution(
        self, currency_code: str, days: int = 30, limit: int = 1000, offset: int = 0
    ) -> List[CotizacionFecha]:
        """
        Get the evolution of a currency's quotation for the last n days.

        :param currency_code: The currency code (e.g., 'USD', 'EUR'). Case-sensitive for URL.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :param limit: Maximum number of results (10-1000), defaults to 1000 for this specific API.
        :param offset: Number of results to skip, defaults to 0.
        :return: A list of CotizacionFecha objects.
        :raises ValueError: If days/limit/offset are invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.get_evolucion_moneda(
            currency_code,
            fecha_desde=start_date.strftime("%Y-%m-%d"),
            fecha_hasta=end_date.strftime("%Y-%m-%d"),
            limit=limit,
            offset=offset,
        )

    def check_denunciado(self, entity_name: str, check_number: int) -> bool:
        """
        Check if a check is reported as stolen or lost.

        :param entity_name: The name of the financial entity (case-insensitive search).
        :param check_number: The check number. Must be positive.
        :return: True if the check is reported, False otherwise.
        :raises ValueError: If the entity is not found or check_number is invalid.
        :raises BCRAApiError: If the API request fails (other than a 404 for the check itself).
        """
        if check_number <= 0:
            raise ValueError("Check number must be positive.")
        try:
            entities = self.get_entidades()
        except BCRAApiError as e:
            self.logger.error(
                f"Could not get entities to check denounced status for '{entity_name}': {e}"
            )
            raise
        normalized_entity_name = entity_name.lower().strip()
        entity = next(
            (
                e
                for e in entities
                if e.denominacion and e.denominacion.lower() == normalized_entity_name
            ),
            None,
        )
        if not entity:
            raise ValueError(f"Entity '{entity_name}' not found")
        try:
            cheque = self.get_cheque_denunciado(entity.codigo_entidad, check_number)
            return cheque.denunciado
        except BCRAApiError as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.logger.info(
                    f"Check {check_number} for entity {entity.codigo_entidad} ({entity_name}) not found, assuming not denounced."
                )
                return False
            self.logger.error(
                f"API error checking denounced status for check {check_number} of entity '{entity_name}': {e}"
            )
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error checking denounced status for check {check_number} of entity '{entity_name}': {e}"
            )
            raise BCRAApiError(
                f"Unexpected error during check verification for '{entity_name}', check {check_number}: {e}"
            ) from e

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

        Calculates rate as (quote_currency_value / base_currency_value) using ARS as intermediary.
        Assumes both currencies are quoted against ARS by the API.

        :param base_currency: The base currency code (e.g., 'USD'). Case-sensitive for URL.
        :param quote_currency: The quote currency code (e.g., 'EUR'). Case-sensitive for URL.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :return: List of dictionaries with 'fecha' (ISO format) and 'tasa' (exchange rate).
        :raises ValueError: If days is invalid.
        :raises BCRAApiError: If underlying API calls fail.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        try:
            limit = (
                days + 15
            )  # Fetch a bit more data to ensure good overlap for daily data
            base_evolution = self.get_currency_evolution(
                base_currency, days, limit=limit
            )
            quote_evolution = self.get_currency_evolution(
                quote_currency, days, limit=limit
            )
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get evolution for currency pair {base_currency}/{quote_currency} due to API error: {e}"
            )
            raise

        base_dict: Dict[date, float] = {}
        for cf in base_evolution:
            if cf.fecha:
                try:
                    base_dict[cf.fecha] = self._get_cotizacion_detalle(
                        cf, base_currency
                    ).tipo_cotizacion
                except ValueError:
                    self.logger.debug(
                        f"Base currency {base_currency} not in cotizacion for {cf.fecha.isoformat()}"
                    )
        quote_dict: Dict[date, float] = {}
        for cf in quote_evolution:
            if cf.fecha:
                try:
                    quote_dict[cf.fecha] = self._get_cotizacion_detalle(
                        cf, quote_currency
                    ).tipo_cotizacion
                except ValueError:
                    self.logger.debug(
                        f"Quote currency {quote_currency} not in cotizacion for {cf.fecha.isoformat()}"
                    )

        pair_evolution = []
        common_dates = sorted(list(set(base_dict.keys()) & set(quote_dict.keys())))
        for d_obj in common_dates:
            base_val = base_dict[d_obj]
            quote_val = quote_dict[d_obj]
            if base_val != 0:  # Avoid division by zero
                rate = quote_val / base_val
                pair_evolution.append({"fecha": d_obj.isoformat(), "tasa": rate})
            else:
                self.logger.warning(
                    f"Base currency {base_currency} had zero value on {d_obj.isoformat()}, cannot calculate pair rate."
                )
        self.logger.info(
            f"Calculated {len(pair_evolution)} data points for {base_currency}/{quote_currency} pair evolution."
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
        Calculate Pearson correlation between two variables/series over last n days (Monetarias v3.0).

        Handles missing data by linear interpolation.

        :param variable_name1: Name of the first variable/series.
        :param variable_name2: Name of the second variable/series.
        :param days: Number of days to look back (must be > 1).
        :return: Correlation coefficient (-1 to 1), or NaN if not calculable.
        :raises ValueError: If variables not found or days invalid.
        :raises BCRAApiError: If underlying API calls fail.
        """
        if days <= 1:
            raise ValueError("Number of days must be greater than 1 for correlation.")
        try:
            data1 = self.get_variable_history(variable_name1, days)
            data2 = self.get_variable_history(variable_name2, days)
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get history for correlation between '{variable_name1}' and '{variable_name2}': {e}"
            )
            raise

        if not data1 or not data2:
            self.logger.warning(
                f"Insufficient data for correlation: '{variable_name1}' ({len(data1)} pts), '{variable_name2}' ({len(data2)} pts)"
            )
            return np.nan

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
            return np.nan

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
            return np.nan
        try:
            correlation, p_value = pearsonr(interp_values1, interp_values2)
        except (
            ValueError
        ) as e:  # Should be caught by constant check, but as a safeguard
            self.logger.error(
                f"Pearsonr calculation failed for '{variable_name1}' and '{variable_name2}': {e}"
            )
            return np.nan

        if np.isnan(correlation):
            self.logger.warning(
                f"Correlation calculation resulted in NaN for '{variable_name1}' and '{variable_name2}'. Check data variability."
            )
            # This can happen if variance is zero for one of the series after interpolation
        else:
            self.logger.info(
                f"Correlation between '{variable_name1}' and '{variable_name2}' ({days} days): {correlation:.4f} (p-value: {p_value:.4f})"
            )
        return float(correlation)

    def generate_variable_report(
        self, variable_name: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a given variable/series (Uses Monetarias v3.0 API).

        :param variable_name: The name of the variable/series.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :return: A dictionary containing various statistics and information.
        :raises ValueError: If the variable is not found or days is invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        variable = self.get_variable_by_name(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")
        try:
            data = self.get_variable_history(variable_name, days)
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

        values = np.array([d.valor for d in data], dtype=float)
        dates = [d.fecha for d in data]

        # Calculate statistics, handling cases where values might be empty
        mean_val = float(np.mean(values)) if values.size > 0 else None
        median_val = float(np.median(values)) if values.size > 0 else None
        min_val = float(np.min(values)) if values.size > 0 else None
        max_val = float(np.max(values)) if values.size > 0 else None
        std_dev_val = float(np.std(values)) if values.size > 0 else None
        latest_val = float(values[-1]) if values.size > 0 else None
        start_val = float(values[0]) if values.size > 0 else None

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
