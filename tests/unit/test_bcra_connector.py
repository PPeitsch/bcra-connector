"""
Test suite for BCRAConnector class covering all methods and functionality.
"""

import time
from datetime import date, datetime
from typing import Any, Callable, Dict, List
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Cheque, ChequeDetalle, Entidad
from bcra_connector.principales_variables import DatosVariable, PrincipalesVariables
from bcra_connector.rate_limiter import RateLimitConfig
from bcra_connector.timeout_config import TimeoutConfig


class TestBCRAConnector:
    """Test cases for BCRAConnector class."""

    @pytest.fixture
    def connector(self) -> BCRAConnector:
        """Create a BCRAConnector instance for testing."""
        return BCRAConnector(verify_ssl=False)

    @pytest.fixture
    def mock_api_response(self) -> Callable[[Dict[str, Any], int], Mock]:
        """Create a mock API response."""

        def _create_response(data: Dict[str, Any], status_code: int = 200) -> Mock:
            response = Mock()
            response.json.return_value = data
            response.status_code = status_code
            return response

        return _create_response

    def test_init_default_values(self) -> None:
        """Test BCRAConnector initialization with default values."""
        connector: BCRAConnector = BCRAConnector()
        assert connector.verify_ssl is True
        assert connector.session.headers["Accept-Language"] == "es-AR"
        assert isinstance(connector.rate_limiter.config, RateLimitConfig)
        assert isinstance(connector.timeout, TimeoutConfig)

    def test_init_custom_values(self) -> None:
        """Test BCRAConnector initialization with custom values."""
        rate_limit: RateLimitConfig = RateLimitConfig(calls=5, period=1.0)
        timeout: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        connector: BCRAConnector = BCRAConnector(
            language="en-US",
            verify_ssl=False,
            debug=True,
            rate_limit=rate_limit,
            timeout=timeout,
        )
        assert connector.verify_ssl is False
        assert connector.session.headers["Accept-Language"] == "en-US"
        assert connector.rate_limiter.config.calls == 5
        assert connector.timeout.connect == 5.0
        assert connector.timeout.read == 30.0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_principales_variables_success(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test successful retrieval of principal variables."""
        mock_data: Dict[str, Any] = {
            "results": [
                {
                    "idVariable": 1,
                    "cdSerie": 246,
                    "descripcion": "Test Variable",
                    "fecha": "2024-03-05",
                    "valor": 100.0,
                }
            ]
        }
        mock_get.return_value = mock_api_response(mock_data, 200)

        connector: BCRAConnector = BCRAConnector()
        result: List[PrincipalesVariables] = connector.get_principales_variables()

        assert len(result) == 1
        assert isinstance(result[0], PrincipalesVariables)
        assert result[0].idVariable == 1
        assert result[0].cdSerie == 246
        assert result[0].descripcion == "Test Variable"
        assert result[0].fecha == date(2024, 3, 5)
        assert result[0].valor == 100.0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_principales_variables_empty_response(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test handling of empty response for principal variables."""
        mock_get.return_value = mock_api_response({"results": []}, 200)

        connector: BCRAConnector = BCRAConnector()
        result: List[PrincipalesVariables] = connector.get_principales_variables()

        assert isinstance(result, list)
        assert len(result) == 0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_datos_variable_success(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test successful retrieval of variable data."""
        mock_data: Dict[str, Any] = {
            "results": [{"idVariable": 1, "fecha": "2024-03-05", "valor": 100.0}]
        }
        mock_get.return_value = mock_api_response(mock_data, 200)

        connector: BCRAConnector = BCRAConnector()
        start_date: datetime = datetime(2024, 3, 1)
        end_date: datetime = datetime(2024, 3, 5)
        result: List[DatosVariable] = connector.get_datos_variable(
            1, start_date, end_date
        )

        assert len(result) == 1
        assert isinstance(result[0], DatosVariable)
        assert result[0].idVariable == 1
        assert result[0].fecha == date(2024, 3, 5)
        assert result[0].valor == 100.0

        # Verify correct URL formation
        expected_url: str = (
            f"{BCRAConnector.BASE_URL}/estadisticas/v2.0/DatosVariable/1/2024-03-01/2024-03-05"
        )
        mock_get.assert_called_once()
        actual_url: str = mock_get.call_args[0][0]
        assert actual_url == expected_url

    def test_get_datos_variable_invalid_dates(self, connector: BCRAConnector) -> None:
        """Test handling of invalid date ranges."""
        # Test end date before start date
        with pytest.raises(ValueError) as exc_info:
            connector.get_datos_variable(1, datetime(2024, 3, 5), datetime(2024, 3, 1))
        assert "'desde' date must be earlier than or equal to 'hasta' date" in str(
            exc_info.value
        )

        # Test date range exceeding one year
        with pytest.raises(ValueError) as exc_info:
            connector.get_datos_variable(1, datetime(2024, 1, 1), datetime(2025, 1, 2))
        assert "Date range must not exceed 1 year" in str(exc_info.value)

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_latest_value_success(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test successful retrieval of latest value."""
        mock_data: Dict[str, Any] = {
            "results": [
                {"idVariable": 1, "fecha": "2024-03-03", "valor": 95.0},
                {"idVariable": 1, "fecha": "2024-03-04", "valor": 97.5},
                {"idVariable": 1, "fecha": "2024-03-05", "valor": 100.0},
            ]
        }
        mock_get.return_value = mock_api_response(mock_data, 200)

        connector: BCRAConnector = BCRAConnector()
        result: DatosVariable = connector.get_latest_value(1)

        assert isinstance(result, DatosVariable)
        assert result.idVariable == 1
        assert result.fecha == date(2024, 3, 5)
        assert result.valor == 100.0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_latest_value_no_data(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test handling of no data for latest value."""
        mock_get.return_value = mock_api_response({"results": []}, 200)

        connector: BCRAConnector = BCRAConnector()
        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_latest_value(1)
        assert "No data available for variable 1" in str(exc_info.value)

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_entidades_success(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test successful retrieval of financial entities."""
        mock_data: Dict[str, Any] = {
            "results": [
                {"codigoEntidad": 11, "denominacion": "BANCO DE LA NACION ARGENTINA"},
                {
                    "codigoEntidad": 14,
                    "denominacion": "BANCO DE LA PROVINCIA DE BUENOS AIRES",
                },
            ]
        }
        mock_get.return_value = mock_api_response(mock_data, 200)

        connector: BCRAConnector = BCRAConnector()
        result: List[Entidad] = connector.get_entidades()

        assert len(result) == 2
        assert all(isinstance(entity, Entidad) for entity in result)
        assert result[0].codigo_entidad == 11
        assert result[1].denominacion == "BANCO DE LA PROVINCIA DE BUENOS AIRES"

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_cheque_denunciado_success(
        self, mock_get: Mock, mock_api_response: Callable[[Dict[str, Any], int], Mock]
    ) -> None:
        """Test successful retrieval of reported check information."""
        mock_data: Dict[str, Any] = {
            "results": {
                "numeroCheque": 20377516,
                "denunciado": True,
                "fechaProcesamiento": "2024-03-05",
                "denominacionEntidad": "BANCO DE LA NACION ARGENTINA",
                "detalles": [
                    {
                        "sucursal": 524,
                        "numeroCuenta": 5240055962,
                        "causal": "Denuncia por robo",
                    }
                ],
            }
        }
        mock_get.return_value = mock_api_response(mock_data, 200)

        connector: BCRAConnector = BCRAConnector()
        result: Cheque = connector.get_cheque_denunciado(11, 20377516)

        assert isinstance(result, Cheque)
        assert result.numero_cheque == 20377516
        assert result.denunciado is True
        assert result.fecha_procesamiento == date(2024, 3, 5)
        assert result.denominacion_entidad == "BANCO DE LA NACION ARGENTINA"
        assert len(result.detalles) == 1
        assert isinstance(result.detalles[0], ChequeDetalle)
        assert result.detalles[0].sucursal == 524
        assert result.detalles[0].numero_cuenta == 5240055962
        assert result.detalles[0].causal == "Denuncia por robo"

    def test_error_handling(self, connector: BCRAConnector) -> None:
        """Test various error handling scenarios."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            # Test timeout
            mock_get.side_effect = Timeout("Request timed out")
            with pytest.raises(BCRAApiError) as exc_info:
                connector.get_principales_variables()
            assert "Request timed out" in str(exc_info.value)

            # Test connection error
            mock_get.side_effect = ConnectionError("Connection failed")
            with pytest.raises(BCRAApiError) as exc_info:
                connector.get_principales_variables()
            assert "API request failed" in str(exc_info.value)

            # Test HTTP error
            mock_get.side_effect = HTTPError("404 Client Error")
            with pytest.raises(BCRAApiError) as exc_info:
                connector.get_principales_variables()
            assert "API request failed" in str(exc_info.value)

    def test_rate_limiting(self, connector: BCRAConnector) -> None:
        """Test rate limiting functionality."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.return_value = Mock(json=lambda: {"results": []}, status_code=200)

            connector.rate_limiter.reset()

            for _ in range(connector.rate_limiter.config.burst):
                delay = connector.rate_limiter.acquire()
                assert delay == 0

            delay = connector.rate_limiter.acquire()
            assert delay > 0
            assert (
                connector.rate_limiter.current_usage
                > connector.rate_limiter.config.calls
            )

    @pytest.mark.parametrize(
        "response_code,error_messages",
        [
            (400, ["Bad Request"]),
            (404, ["Not Found"]),
            (500, ["Internal Server Error"]),
            (429, ["Too Many Requests"]),
        ],
    )
    def test_error_responses(
        self,
        connector: BCRAConnector,
        response_code: int,
        error_messages: List[str],
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
    ) -> None:
        """Test handling of various error responses."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_response: Mock = mock_api_response(
                {"status": response_code, "errorMessages": error_messages},
                response_code,
            )
            mock_response.raise_for_status.side_effect = HTTPError(
                f"{response_code} Error"
            )
            mock_get.return_value = mock_response

            with pytest.raises(BCRAApiError) as exc_info:
                connector.get_principales_variables()

            assert str(response_code) in str(exc_info.value)

    def test_retry_mechanism(self, connector: BCRAConnector) -> None:
        """Test retry mechanism for failed requests."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.side_effect = [
                ConnectionError("First attempt failed"),
                ConnectionError("Second attempt failed"),
                Mock(json=lambda: {"results": []}, status_code=200),
            ]

            result: List[Any] = connector.get_principales_variables()
            assert result == []
            assert mock_get.call_count == 3
