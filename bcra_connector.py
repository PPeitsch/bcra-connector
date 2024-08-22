import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class PrincipalesVariables:
    """
    Represents a principal variable from the BCRA API.

    Attributes:
        id_variable (int): The ID of the variable.
        cd_serie (int): The series code of the variable.
        descripcion (str): The description of the variable.
        fecha (str): The date of the variable's value.
        valor (float): The value of the variable.
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

    Attributes:
        id_variable (int): The ID of the variable.
        fecha (str): The date of the data point.
        valor (float): The value of the variable on the given date.
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

    Attributes:
        BASE_URL (str): The base URL for the BCRA API.
        MAX_RETRIES (int): The maximum number of retries for API requests.
        RETRY_DELAY (int): The delay (in seconds) between retries.
    """

    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v2.0"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, language: str = "es-AR"):
        """
        Initialize the BCRAConnector.
        
        Args:
            language (str): The language for API responses. Defaults to "es-AR".
        """
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Language": language,
            "User-Agent": "BCRAConnector/1.0"
        })

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the BCRA API with retry logic.
        
        Args:
            endpoint (str): The API endpoint to request.
            params (Dict[str, Any], optional): Query parameters for the request.
        
        Returns:
            Dict[str, Any]: The JSON response from the API.
        
        Raises:
            BCRAApiError: If the API request fails after retries.
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    raise BCRAApiError(f"API request failed after {self.MAX_RETRIES} attempts: {str(e)}") from e
                time.sleep(self.RETRY_DELAY * (2 ** attempt))  # Exponential backoff

    def get_principales_variables(self) -> List[PrincipalesVariables]:
        """
        Fetch the list of all variables published by BCRA.
        
        Returns:
            List[PrincipalesVariables]: A list of PrincipalesVariables objects.
        
        Raises:
            BCRAApiError: If the API request fails.
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
        
        Args:
            id_variable (int): The ID of the desired variable.
            desde (datetime): The start date of the range to query.
            hasta (datetime): The end date of the range to query.
        
        Returns:
            List[DatosVariable]: A list of DatosVariable objects.
        
        Raises:
            BCRAApiError: If the API request fails or if the date range is invalid.
            ValueError: If the date range is invalid.
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
        
        Args:
            id_variable (int): The ID of the desired variable.
        
        Returns:
            DatosVariable: The latest data point for the specified variable.
        
        Raises:
            BCRAApiError: If the API request fails or if no data is available.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Look back 30 days to ensure we get data

        data = self.get_datos_variable(id_variable, start_date, end_date)
        if not data:
            raise BCRAApiError(f"No data available for variable {id_variable}")

        return max(data, key=lambda x: datetime.strptime(x.fecha, "%Y-%m-%d"))


# Example usage
if __name__ == "__main__":
    connector = BCRAConnector()

    try:
        # Get all principal variables
        variables = connector.get_principales_variables()
        print("Principal Variables:")
        for var in variables[:5]:  # Print first 5 for brevity
            print(f"{var.descripcion}: {var.valor} ({var.fecha})")

        # Get data for a specific variable (e.g., Reservas Internacionales del BCRA)
        id_variable = 1
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        datos = connector.get_datos_variable(id_variable, start_date, end_date)
        print(f"\nData for Variable {id_variable}:")
        for dato in datos[-5:]:  # Print last 5 for brevity
            print(f"{dato.fecha}: {dato.valor}")

        # Get the latest value for a variable
        latest = connector.get_latest_value(id_variable)
        print(f"\nLatest value for Variable {id_variable}: {latest.valor} ({latest.fecha})")

    except BCRAApiError as e:
        logger.error(f"API Error: {str(e)}")
    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
