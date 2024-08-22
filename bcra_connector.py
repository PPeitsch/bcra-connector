import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import urllib3


@dataclass
class PrincipalesVariables:
    """
    Represents a principal variable from the BCRA API.

    :param id_variable: The ID of the variable
    :type id_variable: int
    :param cd_serie: The series code of the variable
    :type cd_serie: int
    :param descripcion: The description of the variable
    :type descripcion: str
    :param fecha: The date of the variable's value
    :type fecha: str
    :param valor: The value of the variable
    :type valor: float
    """
    id_variable: int
    cd_serie: int
    descripcion: str
    fecha: str
    valor: float


@dataclass
class DatosVariable:
    """
    Represents historical data for a variable.

    :param id_variable: The ID of the variable
    :type id_variable: int
    :param fecha: The date of the data point
    :type fecha: str
    :param valor: The value of the variable on the given date
    :type valor: float
    """
    id_variable: int
    fecha: str
    valor: float


class BCRAApiError(Exception):
    """Custom exception for BCRA API errors."""
    pass


class BCRAConnector:
    """
    A connector for the BCRA (Banco Central de la República Argentina) Estadísticas API v2.0.
    
    This class provides methods to interact with the BCRA API, including fetching principal
    variables and historical data for specific variables.

    :param language: The language for API responses, defaults to "es-AR"
    :type language: str, optional
    :param verify_ssl: Whether to verify SSL certificates, defaults to True
    :type verify_ssl: bool, optional
    :param debug: Whether to enable debug logging, defaults to False
    :type debug: bool, optional
    """

    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v2.0"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, language: str = "es-AR", verify_ssl: bool = True, debug: bool = False):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Language": language,
            "User-Agent": "BCRAConnector/1.0"
        })
        self.verify_ssl = verify_ssl

        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        if not self.verify_ssl:
            self.logger.warning("SSL verification is disabled. This is not recommended for production use.")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the BCRA API with retry logic.
        
        :param endpoint: The API endpoint to request
        :type endpoint: str
        :param params: Query parameters for the request, defaults to None
        :type params: Dict[str, Any], optional
        
        :return: The JSON response from the API
        :rtype: Dict[str, Any]
        
        :raises BCRAApiError: If the API request fails after retries
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, verify=self.verify_ssl)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(f"API request failed after {self.MAX_RETRIES} attempts: {str(e)}") from e
                time.sleep(self.RETRY_DELAY * (2 ** attempt))  # Exponential backoff

    def get_principales_variables(self) -> List[PrincipalesVariables]:
        """
        Fetch the list of all variables published by BCRA.
        
        :return: A list of PrincipalesVariables objects
        :rtype: List[PrincipalesVariables]
        
        :raises BCRAApiError: If the API request fails
        """
        try:
            data = self._make_request("PrincipalesVariables")
            return [
                PrincipalesVariables(
                    id_variable=item['idVariable'],
                    cd_serie=item['cdSerie'],
                    descripcion=item['descripcion'],
                    fecha=item['fecha'],
                    valor=item['valor']
                )
                for item in data['results']
            ]
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

    def get_datos_variable(self, id_variable: int, desde: datetime, hasta: datetime) -> List[DatosVariable]:
        """
        Fetch the list of values for a variable within a specified date range.
        
        :param id_variable: The ID of the desired variable
        :type id_variable: int
        :param desde: The start date of the range to query
        :type desde: datetime
        :param hasta: The end date of the range to query
        :type hasta: datetime
        
        :return: A list of DatosVariable objects
        :rtype: List[DatosVariable]
        
        :raises BCRAApiError: If the API request fails or if the date range is invalid
        :raises ValueError: If the date range is invalid
        """
        if desde > hasta:
            raise ValueError("'desde' date must be earlier than or equal to 'hasta' date")

        if hasta - desde > timedelta(days=365):
            raise ValueError("Date range must not exceed 1 year")

        try:
            data = self._make_request(
                f"DatosVariable/{id_variable}/{desde.date()}/{hasta.date()}"
            )
            return [
                DatosVariable(
                    id_variable=item['idVariable'],
                    fecha=item['fecha'],
                    valor=item['valor']
                )
                for item in data['results']
            ]
        except KeyError as e:
            raise BCRAApiError(f"Unexpected response format: {str(e)}") from e

    def get_latest_value(self, id_variable: int) -> DatosVariable:
        """
        Fetch the latest value for a specific variable.
        
        :param id_variable: The ID of the desired variable
        :type id_variable: int
        
        :return: The latest data point for the specified variable
        :rtype: DatosVariable
        
        :raises BCRAApiError: If the API request fails or if no data is available
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Look back 30 days to ensure we get data

        data = self.get_datos_variable(id_variable, start_date, end_date)
        if not data:
            raise BCRAApiError(f"No data available for variable {id_variable}")

        return max(data, key=lambda x: datetime.strptime(x.fecha, "%Y-%m-%d"))
