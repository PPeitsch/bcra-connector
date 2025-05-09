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
import urllib3
from scipy.stats import pearsonr
from urllib3.exceptions import SSLError as URLLibSSLError

# Assuming these imports might need adjustment based on model changes later
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
    Principales Variables (Monetarias v3.0), Cheques, and Estadísticas Cambiarias.
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

                self.logger.debug(f"Making request to {url} with params {params}")
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
                        # Provide more context from the response if possible
                        error_msg = f"HTTP 404: Resource not found at {response.url}"
                        try:
                            error_data = response.json()
                            if "errorMessages" in error_data:
                                error_msg += (
                                    f": {', '.join(error_data['errorMessages'])}"
                                )
                        except (ValueError, KeyError, json.JSONDecodeError):
                            pass  # Stick with the basic 404 message
                        raise BCRAApiError(error_msg) from e

                    error_msg = f"HTTP {status_code} for {response.url}"
                    try:
                        error_data = response.json()
                        if "errorMessages" in error_data:
                            error_msg = (
                                f"{error_msg}: {', '.join(error_data['errorMessages'])}"
                            )
                        elif isinstance(
                            error_data, dict
                        ):  # Handle other potential error structures
                            error_msg += f": {str(error_data)}"

                    except (ValueError, KeyError, json.JSONDecodeError):
                        # If JSON parsing fails or no errorMessages, use reason
                        error_msg = f"{error_msg}: {response.reason}"

                    raise BCRAApiError(error_msg) from e

                try:
                    return dict(response.json())
                except (ValueError, json.JSONDecodeError) as e:
                    raise BCRAApiError(f"Invalid JSON response from {url}") from e

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
                # Distinguish SSL errors
                if isinstance(e, URLLibSSLError) or "SSL" in str(e).upper():
                    raise BCRAApiError(f"SSL verification failed for {url}") from e

                self.logger.warning(
                    f"Connection error to {url} (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(
                        f"API request failed: Connection error to {url}"
                    ) from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

            except requests.RequestException as e:
                # Catch other potential requests exceptions
                self.logger.error(
                    f"API request exception for {url}: {e} (attempt {attempt+1}/{self.MAX_RETRIES})"
                )
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(
                        f"API request failed after {self.MAX_RETRIES} attempts: {str(e)}"
                    ) from e
                time.sleep(self.RETRY_DELAY * (2**attempt))

        # This should technically be unreachable if MAX_RETRIES > 0, but added for safety
        raise BCRAApiError("Maximum retry attempts reached")

    # Principales Variables / Monetarias methods (v3.0)
    def get_principales_variables(self) -> List[PrincipalesVariables]:
        """
        Fetch the list of all monetary series and principal variables published by BCRA (API v3.0).

        :return: A list of PrincipalesVariables objects (Note: structure changed in v3.0, 'categoria' added, 'cdSerie' removed)
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info("Fetching monetary series and principal variables (v3.0)")
        try:
            # --- UPDATED ENDPOINT ---
            data = self._make_request("estadisticas/v3.0/monetarias")
            # --- END UPDATE ---

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
                    # Note: PrincipalesVariables.from_dict needs update in Step 1.3
                    variables.append(PrincipalesVariables.from_dict(item))
                except (KeyError, ValueError) as e:
                    self.logger.warning(
                        f"Skipping invalid variable data: {str(e)} - Data: {item}"
                    )

            if not variables and data["results"]:
                self.logger.error(
                    "Failed to parse any variable data despite receiving results."
                )
            elif not variables:
                self.logger.warning("No valid variables found in the response")
            else:
                self.logger.info(
                    f"Successfully fetched and parsed {len(variables)} variables (v3.0)"
                )

            return variables
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching principal variables (v3.0): {str(e)}"
            self.logger.exception(
                error_msg
            )  # Use logger.exception to include traceback
            raise BCRAApiError(error_msg) from e

    def get_datos_variable(
        self,
        id_variable: int,
        desde: Optional[datetime] = None,  # Made optional as per v3.0 docs logic
        hasta: Optional[datetime] = None,  # Made optional
        limit: Optional[int] = None,  # Added limit
        offset: Optional[int] = None,  # Added offset
        # ) -> List[DatosVariable]: # NOTE: Return type will change in Step 1.3
    ) -> Dict[str, Any]:  # Temporary return type until DatosVariableResponse is added
        """
        Fetch the list of values for a variable within a specified date range (API v3.0).

        Uses pagination via limit and offset. If desde/hasta are omitted, API defaults apply.
        The raw dictionary response is returned temporarily until models are updated.

        :param id_variable: The ID of the desired variable. Case-sensitive `{IdVariable}` in URL path.
        :param desde: The start date of the range to query (inclusive). Optional. YYYY-MM-DD format.
        :param hasta: The end date of the range to query (inclusive). Optional. YYYY-MM-DD format.
        :param limit: Maximum number of results (10-3000). Optional, API defaults to 1000.
        :param offset: Number of results to skip for pagination. Optional, defaults to 0.
        :return: Raw dictionary response from API (Includes 'metadata' and 'results').
                 (NOTE: This will change to return a DatosVariableResponse object in Step 1.3)
        :raises ValueError: If date range is invalid or limit/offset are out of bounds.
        :raises BCRAApiError: If the API request fails.
        """
        log_msg = f"Fetching data for variable {id_variable}"
        if desde:
            log_msg += f" from {desde.date()}"
        if hasta:
            log_msg += f" to {hasta.date()}"
        if limit is not None:
            log_msg += f" limit {limit}"
        if offset is not None:
            log_msg += f" offset {offset}"
        self.logger.info(log_msg + " (v3.0)")

        # --- VALIDATION ---
        if desde and hasta and desde > hasta:
            raise ValueError(
                "'desde' date must be earlier than or equal to 'hasta' date"
            )

        # Removed 1-year limit check as per v3.0

        if limit is not None and not (10 <= limit <= 3000):
            raise ValueError("Limit must be between 10 and 3000")

        if offset is not None and offset < 0:
            raise ValueError("Offset must be non-negative")
        # --- END VALIDATION ---

        # --- REQUEST LOGIC ---
        params: Dict[str, Any] = {}
        if desde:
            params["desde"] = desde.strftime("%Y-%m-%d")
        if hasta:
            params["hasta"] = hasta.strftime("%Y-%m-%d")
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        # Using id_variable in the path as documented {IdVariable} in v3.0
        endpoint = f"estadisticas/v3.0/monetarias/{id_variable}"

        try:
            # Return the raw data for now, parsing will happen in Step 1.3
            data = self._make_request(endpoint, params=params if params else None)
            self.logger.info(
                f"Successfully received raw data for variable {id_variable} (v3.0)"
            )
            # Basic check for expected structure
            if "results" not in data or "metadata" not in data:
                self.logger.warning(
                    f"Response for {id_variable} might be missing expected keys ('results', 'metadata')."
                )
            return data

        except BCRAApiError:
            self.logger.error(f"API Error fetching data for variable {id_variable}")
            raise
        except Exception as e:
            error_msg = f"Unexpected error fetching data for variable {id_variable} (v3.0): {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e
        # --- END REQUEST LOGIC ---

    def get_latest_value(self, id_variable: int) -> DatosVariable:
        """
        Fetch the latest value for a specific variable using API v3.0.

        Note: This implementation currently parses the raw response. It will be
        updated in Step 1.3 to use the new DatosVariableResponse model.

        :param id_variable: The ID of the desired variable.
        :return: The latest data point (DatosVariable object) for the specified variable.
        :raises BCRAApiError: If the API request fails or if no data is available.
        """
        self.logger.info(
            f"Fetching latest value for variable {id_variable} (using v3.0 logic)"
        )

        # Fetch recent records using the v3.0 endpoint (limit=10 should be enough)
        # NOTE: This needs update when get_datos_variable returns DatosVariableResponse
        raw_data = self.get_datos_variable(id_variable, limit=10)

        # --- TEMPORARY PARSING LOGIC (Start) ---
        if not raw_data or "results" not in raw_data or not raw_data["results"]:
            # If no data with limit 10, try looking back further - 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            self.logger.info(
                f"No recent data found for {id_variable}, checking last 30 days."
            )
            raw_data = self.get_datos_variable(
                id_variable, desde=start_date, hasta=end_date
            )
            if not raw_data or "results" not in raw_data or not raw_data["results"]:
                raise BCRAApiError(
                    f"No data available for variable {id_variable} in the last 30 days."
                )

        # Parse the results list from the raw data
        try:
            data_list = [DatosVariable.from_dict(item) for item in raw_data["results"]]
        except (KeyError, ValueError) as e:
            self.logger.error(
                f"Failed to parse data points for latest value of {id_variable}: {e}"
            )
            raise BCRAApiError(
                f"Could not parse data for variable {id_variable}"
            ) from e

        if not data_list:
            raise BCRAApiError(
                f"No parsable data points found for variable {id_variable}"
            )

        # Sort by date descending and take the first one
        latest = max(data_list, key=lambda x: x.fecha)
        # --- TEMPORARY PARSING LOGIC (End) ---

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
            # Added check for 'results' key
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError("Invalid response format for entities endpoint")
            entities = [Entidad.from_dict(e) for e in data["results"]]
            self.logger.info(f"Successfully fetched {len(entities)} entities")
            return entities
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e
        except Exception as e:
            error_msg = f"Error fetching financial entities: {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

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
            # Added check for 'results' key
            if "results" not in data or not isinstance(data["results"], dict):
                raise BCRAApiError(
                    "Invalid response format for reported check endpoint"
                )
            return Cheque.from_dict(data["results"])
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e
        except BCRAApiError:
            raise  # Re-raise specific API errors
        except Exception as e:
            error_msg = f"Error fetching reported check {numero_cheque}: {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

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
            # Added check for 'results' key
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError("Invalid response format for currencies endpoint")
            divisas = [
                Divisa.from_dict(d) for d in data["results"]
            ]  # Use from_dict for consistency
            self.logger.info(f"Successfully fetched {len(divisas)} currencies")
            return divisas
        except (KeyError, ValueError) as e:  # Catch potential parsing errors too
            raise BCRAApiError(f"Unexpected response format or data: {str(e)}") from e
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching currencies: {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    def get_cotizaciones(self, fecha: Optional[str] = None) -> CotizacionFecha:
        """
        Fetch currency quotations for a specific date.

        :param fecha: The date for which to fetch quotations (format: YYYY-MM-DD), defaults to None (latest date)
        :return: A CotizacionFecha object with the quotations
        :raises BCRAApiError: If the API request fails or returns unexpected data
        :raises ValueError: If the date format is invalid (handled by API or potentially requests)
        """
        self.logger.info(
            f"Fetching quotations for date: {fecha if fecha else 'latest'}"
        )
        try:
            params = {"fecha": fecha} if fecha else None
            data = self._make_request(
                "estadisticascambiarias/v1.0/Cotizaciones", params
            )
            # Added check for 'results' key
            if "results" not in data or not isinstance(data["results"], dict):
                raise BCRAApiError("Invalid response format for quotations endpoint")

            cotizacion = CotizacionFecha.from_dict(data["results"])
            fecha_log = cotizacion.fecha if cotizacion.fecha else "latest available"
            self.logger.info(f"Successfully fetched quotations for {fecha_log}")
            return cotizacion
        except (KeyError, ValueError) as e:  # Catch potential parsing errors
            raise BCRAApiError(f"Unexpected response format or data: {str(e)}") from e
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching quotations for date {fecha}: {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    def get_evolucion_moneda(
        self,
        moneda: str,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limit: int = 1000,  # Default matches API doc
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
            raise ValueError("Limit must be between 10 and 1000")
        if offset < 0:
            raise ValueError("Offset must be non-negative")

        try:
            params = {
                "fechaDesde": fecha_desde,
                "fechaHasta": fecha_hasta,
                "limit": limit,
                "offset": offset,
            }
            # Remove None values before sending params
            params = {k: v for k, v in params.items() if v is not None}

            endpoint = f"estadisticascambiarias/v1.0/Cotizaciones/{moneda}"
            data = self._make_request(endpoint, params=params if params else None)

            # Added check for 'results' key
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError(
                    f"Invalid response format for currency evolution endpoint ({moneda})"
                )

            evolucion = [CotizacionFecha.from_dict(cf) for cf in data["results"]]
            self.logger.info(
                f"Successfully fetched {len(evolucion)} data points for {moneda}"
            )
            return evolucion
        except (KeyError, ValueError) as e:  # Catch parsing errors
            raise BCRAApiError(
                f"Unexpected response format or data for {moneda}: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching evolution for {moneda}: {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    # --- Helper Methods ---

    def get_variable_by_name(
        self, variable_name: str
    ) -> Optional[PrincipalesVariables]:
        """
        Find a principal variable or monetary series by its name (Uses v3.0 API).

        :param variable_name: The name of the variable/series to find (case-insensitive search).
        :return: A PrincipalesVariables object if found, None otherwise.
        """
        try:
            variables = self.get_principales_variables()  # Uses v3.0
        except BCRAApiError as e:
            self.logger.error(f"Failed to get variables to search by name: {e}")
            return None  # Or re-raise depending on desired behavior

        normalized_name = variable_name.lower().strip()
        for variable in variables:
            # Description field still exists in v3.0 response
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
        limit: Optional[int] = None,  # Allow passing limit through
        offset: Optional[int] = None,  # Allow passing offset through
        # ) -> List[DatosVariable]: # NOTE: Return type will change in Step 1.3
    ) -> Dict[str, Any]:  # Temporary return type
        """
        Get the historical data for a variable/series by name for the last n days (Uses v3.0 API).

        Returns the raw dictionary response temporarily.

        :param variable_name: The name of the variable/series.
        :param days: The number of days to look back, defaults to 30.
        :param limit: Maximum number of results (10-3000). Optional.
        :param offset: Number of results to skip for pagination. Optional.
        :return: Raw dictionary response from API. (NOTE: This will change to DatosVariableResponse).
        :raises ValueError: If the variable is not found or days/limit/offset are invalid.
        :raises BCRAApiError: If the API request fails.
        """
        variable = self.get_variable_by_name(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=max(1, days))  # Ensure at least 1 day

        # This now uses the v3.0 endpoint implicitly
        # NOTE: Needs update when get_datos_variable returns DatosVariableResponse
        return self.get_datos_variable(
            variable.idVariable,
            desde=start_date,
            hasta=end_date,
            limit=limit,
            offset=offset,
        )

    def get_currency_evolution(
        self,
        currency_code: str,
        days: int = 30,
        limit: int = 1000,  # Use API max as default limit for evolution
        offset: int = 0,
    ) -> List[CotizacionFecha]:
        """
        Get the evolution of a currency's quotation for the last n days.

        :param currency_code: The currency code (e.g., 'USD', 'EUR'). Case-sensitive for URL.
        :param days: The number of days to look back, defaults to 30.
        :param limit: Maximum number of results (10-1000), defaults to 1000.
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
        :param check_number: The check number.
        :return: True if the check is reported, False otherwise.
        :raises ValueError: If the entity is not found or check_number is invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if check_number <= 0:
            raise ValueError("Check number must be positive.")

        try:
            entities = self.get_entidades()
        except BCRAApiError as e:
            self.logger.error(f"Could not get entities to check denounced status: {e}")
            raise  # Re-raise API error

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
            # Note: get_cheque_denunciado can raise BCRAApiError (e.g., 404 if check not found)
            cheque = self.get_cheque_denunciado(entity.codigo_entidad, check_number)
            # If the API call succeeds, the 'denunciado' field indicates the status
            return cheque.denunciado
        except BCRAApiError as e:
            # Handle 404 specifically: Check not found means it's not denounced
            if "404" in str(e):
                self.logger.info(
                    f"Check {check_number} for entity {entity.codigo_entidad} not found, assuming not denounced."
                )
                return False
            # Re-raise other API errors
            self.logger.error(
                f"API error checking denounced status for check {check_number}: {e}"
            )
            raise
        except Exception as e:
            # Catch unexpected errors during the check process
            self.logger.exception(
                f"Unexpected error checking denounced status for check {check_number}: {e}"
            )
            raise BCRAApiError(
                f"Unexpected error during check verification: {e}"
            ) from e

    def get_latest_quotations(self) -> Dict[str, float]:
        """
        Get the latest quotations (tipo_cotizacion) for all currencies.

        :return: A dictionary with currency codes as keys and their latest quotations as values.
        :raises BCRAApiError: If fetching quotations fails.
        """
        try:
            cotizaciones = self.get_cotizaciones()  # Gets latest by default
        except BCRAApiError as e:
            self.logger.error(f"Failed to get latest quotations: {e}")
            raise  # Re-raise API error

        if not cotizaciones or not cotizaciones.detalle:
            self.logger.warning(
                "No quotation details found in the latest API response."
            )
            return {}

        return {
            detail.codigo_moneda: detail.tipo_cotizacion
            for detail in cotizaciones.detalle
            if detail.codigo_moneda  # Ensure code is not empty
        }

    def get_currency_pair_evolution(
        self, base_currency: str, quote_currency: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get the evolution of a currency pair exchange rate for the last n days.

        Calculates the rate as (quote_currency_value / base_currency_value) in ARS terms.
        Assumes both currencies are quoted against ARS by the API.

        :param base_currency: The base currency code (e.g., 'USD'). Case-sensitive for URL.
        :param quote_currency: The quote currency code (e.g., 'EUR'). Case-sensitive for URL.
        :param days: The number of days to look back, defaults to 30.
        :return: A list of dictionaries containing 'fecha' (ISO format) and 'tasa' (exchange rate).
                 Returns empty list if data is insufficient or calculation is not possible.
        :raises ValueError: If days is invalid.
        :raises BCRAApiError: If underlying API calls fail.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")

        try:
            # Fetch evolution for both currencies concurrently? (Future enhancement: asyncio)
            # Limit fetched data points based on days for efficiency
            limit = days + 5  # Fetch slightly more than needed days
            base_evolution = self.get_currency_evolution(
                base_currency, days, limit=limit
            )
            quote_evolution = self.get_currency_evolution(
                quote_currency, days, limit=limit
            )
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get evolution for currency pair {base_currency}/{quote_currency}: {e}"
            )
            raise  # Re-raise API error

        # Prepare dictionaries mapping date -> quotation value (tipo_cotizacion)
        base_dict: Dict[date, float] = {}
        for cf in base_evolution:
            if cf.fecha:  # Ensure date is not None
                try:
                    detail = self._get_cotizacion_detalle(cf, base_currency)
                    base_dict[cf.fecha] = detail.tipo_cotizacion
                except ValueError:
                    self.logger.warning(
                        f"Base currency {base_currency} not found in cotizacion for {cf.fecha}"
                    )

        quote_dict: Dict[date, float] = {}
        for cf in quote_evolution:
            if cf.fecha:  # Ensure date is not None
                try:
                    detail = self._get_cotizacion_detalle(cf, quote_currency)
                    quote_dict[cf.fecha] = detail.tipo_cotizacion
                except ValueError:
                    self.logger.warning(
                        f"Quote currency {quote_currency} not found in cotizacion for {cf.fecha}"
                    )

        pair_evolution = []
        # Find common dates where both currencies have data
        common_dates = sorted(list(set(base_dict.keys()) & set(quote_dict.keys())))

        for d in common_dates:
            base_val = base_dict[d]
            quote_val = quote_dict[d]

            if base_val != 0:  # Avoid division by zero
                rate = quote_val / base_val
                pair_evolution.append({"fecha": d.isoformat(), "tasa": rate})
            else:
                self.logger.warning(
                    f"Base currency {base_currency} had zero value on {d}, cannot calculate pair rate."
                )

        self.logger.info(
            f"Calculated {len(pair_evolution)} data points for {base_currency}/{quote_currency} pair."
        )
        return pair_evolution  # Already sorted by date due to common_dates being sorted

    @staticmethod
    def _get_cotizacion_detalle(
        cotizacion_fecha: CotizacionFecha, currency_code: str
    ) -> CotizacionDetalle:
        """
        Helper method to get CotizacionDetalle for a specific currency from CotizacionFecha.

        :param cotizacion_fecha: CotizacionFecha object.
        :param currency_code: The currency code to look for.
        :return: CotizacionDetalle for the specified currency.
        :raises ValueError: If the currency is not found in the CotizacionFecha.
        """
        if not cotizacion_fecha or not cotizacion_fecha.detalle:
            raise ValueError(
                f"Invalid CotizacionFecha object provided for currency {currency_code}."
            )

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
        Calculate the Pearson correlation between two variables/series over the last n days (Uses v3.0 API).

        Handles missing data by linear interpolation based on dates.

        :param variable_name1: The name of the first variable/series.
        :param variable_name2: The name of the second variable/series.
        :param days: The number of days to look back, defaults to 30.
        :return: The correlation coefficient (between -1 and 1), or NaN if calculation is not possible.
        :raises ValueError: If either variable is not found or days is invalid.
        :raises BCRAApiError: If underlying API calls fail.
        """
        if days <= 1:  # Need at least 2 data points for correlation
            raise ValueError("Number of days must be greater than 1 for correlation.")

        # NOTE: This needs update when get_variable_history changes return type
        try:
            raw_data1 = self.get_variable_history(variable_name1, days)
            raw_data2 = self.get_variable_history(variable_name2, days)
        except BCRAApiError as e:
            self.logger.error(f"Failed to get history for correlation: {e}")
            raise  # Re-raise API error

        # --- TEMPORARY PARSING (Start) ---
        try:
            data1 = [
                DatosVariable.from_dict(item) for item in raw_data1.get("results", [])
            ]
            data2 = [
                DatosVariable.from_dict(item) for item in raw_data2.get("results", [])
            ]
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse data for correlation: {e}")
            raise BCRAApiError(
                "Could not parse data for correlation calculation"
            ) from e
        # --- TEMPORARY PARSING (End) ---

        if not data1 or not data2:
            self.logger.warning(
                f"Insufficient data for correlation between '{variable_name1}' and '{variable_name2}'"
            )
            return np.nan  # Return NaN if either dataset is empty

        # Extract dates and values
        dates1 = [d.fecha for d in data1]
        dates2 = [d.fecha for d in data2]
        values1 = np.array([d.valor for d in data1], dtype=float)  # Use numpy array
        values2 = np.array([d.valor for d in data2], dtype=float)  # Use numpy array

        # Check for sufficient unique dates
        if len(set(dates1)) < 2 or len(set(dates2)) < 2:
            self.logger.warning(
                f"Insufficient unique dates for correlation between '{variable_name1}' and '{variable_name2}'"
            )
            return np.nan

        # Create a common, sorted date range (as ordinals for interpolation)
        all_dates_ord = np.array(
            sorted(list(set(d.toordinal() for d in dates1 + dates2))), dtype=float
        )
        dates1_ord = np.array([d.toordinal() for d in dates1], dtype=float)
        dates2_ord = np.array([d.toordinal() for d in dates2], dtype=float)

        # Interpolate missing values onto the common date range
        # np.interp requires x-coordinates (dates) to be increasing. Sort data first.
        sort_idx1 = np.argsort(dates1_ord)
        sort_idx2 = np.argsort(dates2_ord)
        interp_values1 = np.interp(
            all_dates_ord, dates1_ord[sort_idx1], values1[sort_idx1]
        )
        interp_values2 = np.interp(
            all_dates_ord, dates2_ord[sort_idx2], values2[sort_idx2]
        )

        # Check for constant series after interpolation (can lead to NaN correlation)
        if np.all(interp_values1 == interp_values1[0]) or np.all(
            interp_values2 == interp_values2[0]
        ):
            self.logger.warning(
                f"Cannot calculate correlation for '{variable_name1}' and '{variable_name2}' due to constant data after interpolation."
            )
            return np.nan

        # Calculate correlation
        try:
            correlation, p_value = pearsonr(interp_values1, interp_values2)
        except ValueError as e:
            # Catch potential issues like NaN inputs if interpolation failed unexpectedly
            self.logger.error(
                f"Pearsonr calculation failed for '{variable_name1}' and '{variable_name2}': {e}"
            )
            return np.nan

        if np.isnan(correlation):
            self.logger.warning(
                f"Correlation calculation resulted in NaN for '{variable_name1}' and '{variable_name2}'. Check data variability."
            )
            return np.nan

        self.logger.info(
            f"Correlation between '{variable_name1}' and '{variable_name2}' ({days} days): {correlation:.4f} (p-value: {p_value:.4f})"
        )
        return float(correlation)

    def generate_variable_report(
        self, variable_name: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a given variable/series (Uses v3.0 API).

        Note: Uses temporary parsing logic until models are updated in Step 1.3.

        :param variable_name: The name of the variable/series.
        :param days: The number of days to look back, defaults to 30.
        :return: A dictionary containing various statistics and information.
        :raises ValueError: If the variable is not found or days is invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")

        variable = self.get_variable_by_name(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")

        # NOTE: Needs update when get_variable_history changes return type
        try:
            raw_data = self.get_variable_history(variable_name, days)
        except BCRAApiError as e:
            self.logger.error(f"Failed to get history for report generation: {e}")
            # Return error within the report structure? Or re-raise? Let's re-raise.
            raise

        # --- TEMPORARY PARSING (Start) ---
        try:
            data = [
                DatosVariable.from_dict(item) for item in raw_data.get("results", [])
            ]
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse data for report generation: {e}")
            raise BCRAApiError("Could not parse data for report generation") from e
        # --- TEMPORARY PARSING (End) ---

        if not data:
            self.logger.warning(
                f"No data available for report on '{variable_name}' for the last {days} days."
            )
            # Return a minimal report indicating no data
            return {
                "variable_name": variable_name,
                "variable_id": variable.idVariable,
                "description": variable.descripcion,
                "category": getattr(
                    variable, "categoria", "N/A"
                ),  # Use updated model field
                "period": f"Last {days} days",
                "error": "No data available for the specified period",
            }

        # Extract values and dates, use numpy for stats
        values = np.array([d.valor for d in data], dtype=float)
        dates = [d.fecha for d in data]  # Keep as list of dates

        # Calculate statistics safely
        mean_val = float(np.mean(values)) if values.size > 0 else None
        median_val = float(np.median(values)) if values.size > 0 else None
        min_val = float(np.min(values)) if values.size > 0 else None
        max_val = float(np.max(values)) if values.size > 0 else None
        std_dev_val = float(np.std(values)) if values.size > 0 else None
        latest_val = float(values[-1]) if values.size > 0 else None
        start_val = float(values[0]) if values.size > 0 else None
        latest_date_iso = dates[-1].isoformat() if dates else None
        start_date_iso = dates[0].isoformat() if dates else None

        percent_change_val = None
        if latest_val is not None and start_val is not None and start_val != 0:
            percent_change_val = (latest_val - start_val) / start_val * 100.0

        report = {
            "variable_name": variable_name,
            "variable_id": variable.idVariable,
            "description": variable.descripcion,
            # Add categoria if PrincipalesVariables model includes it after update
            "category": getattr(
                variable, "categoria", "N/A"
            ),  # Use updated model field
            "period": f"Last {days} days",
            "start_date": start_date_iso,
            "end_date": latest_date_iso,
            "latest_value": latest_val,
            "latest_date": latest_date_iso,
            "min_value": min_val,
            "max_value": max_val,
            "mean_value": mean_val,
            "median_value": median_val,
            "std_dev": std_dev_val,
            "data_points": len(values),
            "percent_change": percent_change_val,
            # Add unit if available (assuming model might have it later)
            # "unit": getattr(variable, "unidad", "N/A"),
        }

        self.logger.info(f"Generated report for '{variable_name}' over {days} days.")
        return report
