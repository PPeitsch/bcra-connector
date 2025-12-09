"""
Test suite for BCRAConnector class covering all methods and functionality.
"""

from datetime import date, datetime
from typing import Any, Callable, Dict, List
from unittest.mock import ANY, Mock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Cheque, Entidad
from bcra_connector.principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
from bcra_connector.rate_limiter import RateLimitConfig
from bcra_connector.timeout_config import TimeoutConfig


class TestBCRAConnector:
    """Test cases for BCRAConnector class."""

    @pytest.fixture
    def connector(self) -> BCRAConnector:
        """Create a BCRAConnector instance for testing."""
        return BCRAConnector(
            verify_ssl=False, rate_limit=RateLimitConfig(calls=100, period=1.0)
        )

    @pytest.fixture
    def mock_api_response(self) -> Callable[[Dict[str, Any], int], Mock]:
        """Create a mock API response."""

        def _create_response(data: Dict[str, Any], status_code: int = 200) -> Mock:
            response = Mock()
            response.json.return_value = data
            response.status_code = status_code
            if status_code >= 400:
                response.raise_for_status.side_effect = HTTPError(response=response)
            else:
                response.raise_for_status.return_value = None
            return response

        return _create_response

    def test_init_default_values(self) -> None:
        """Test BCRAConnector initialization with default values."""
        connector_instance: BCRAConnector = BCRAConnector()
        assert connector_instance.verify_ssl is True
        assert connector_instance.session.headers["Accept-Language"] == "es-AR"
        assert isinstance(connector_instance.rate_limiter.config, RateLimitConfig)
        assert isinstance(connector_instance.timeout, TimeoutConfig)

    def test_init_custom_values(self) -> None:
        """Test BCRAConnector initialization with custom values."""
        rate_limit: RateLimitConfig = RateLimitConfig(calls=5, period=1.0)
        timeout: TimeoutConfig = TimeoutConfig(connect=5.0, read=30.0)
        connector_instance: BCRAConnector = BCRAConnector(
            language="en-US",
            verify_ssl=False,
            debug=True,
            rate_limit=rate_limit,
            timeout=timeout,
        )
        assert connector_instance.verify_ssl is False
        assert connector_instance.session.headers["Accept-Language"] == "en-US"
        assert connector_instance.rate_limiter.config.calls == 5
        assert connector_instance.timeout.connect == 5.0
        assert connector_instance.timeout.read == 30.0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_principales_variables_success_v3(
        self,
        mock_get: Mock,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
        connector: BCRAConnector,
    ) -> None:
        """Test successful retrieval of principal variables (v4.0 format)."""
        mock_data_v4: Dict[str, Any] = {
            "results": [
                {
                    "idVariable": 1,
                    "descripcion": "Test Variable v4",
                    "categoria": "Indicadores Monetarios",
                    "tipoSerie": "Diaria",
                    "periodicidad": "D",
                    "unidadExpresion": "Millones",
                    "moneda": "ARS",
                    "primerFechaInformada": "2020-01-01",
                    "ultFechaInformada": "2024-03-05",
                    "ultValorInformado": 100.0,
                }
            ]
        }
        mock_get.return_value = mock_api_response(mock_data_v4, 200)
        result: List[PrincipalesVariables] = connector.get_principales_variables()

        mock_get.assert_called_once_with(
            f"{BCRAConnector.BASE_URL}/estadisticas/v4.0/Monetarias",
            params=None,
            verify=False,
            timeout=ANY,
        )
        assert len(result) == 1
        pv = result[0]
        assert isinstance(pv, PrincipalesVariables)
        assert pv.idVariable == 1
        assert pv.descripcion == "Test Variable v4"
        assert pv.categoria == "Indicadores Monetarios"
        assert pv.ultValorInformado == 100.0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_principales_variables_empty_response_v3(
        self,
        mock_get: Mock,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
        connector: BCRAConnector,
    ) -> None:
        """Test handling of empty response for principal variables (v4.0)."""
        mock_get.return_value = mock_api_response({"results": []}, 200)
        result: List[PrincipalesVariables] = connector.get_principales_variables()

        assert isinstance(result, list)
        assert len(result) == 0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_datos_variable_success_v3(
        self,
        mock_get: Mock,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
        connector: BCRAConnector,
    ) -> None:
        """Test successful retrieval of variable data (v4.0 format)."""
        mock_data_v4: Dict[str, Any] = {
            "status": 200,
            "metadata": {"resultset": {"count": 2, "offset": 0, "limit": 10}},
            "results": [
                {
                    "idVariable": 1,
                    "detalle": [
                        {"fecha": "2024-03-04", "valor": 95.0},
                        {"fecha": "2024-03-05", "valor": 100.0},
                    ],
                }
            ],
        }
        mock_get.return_value = mock_api_response(mock_data_v4, 200)

        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 3, 5)

        response: DatosVariableResponse = connector.get_datos_variable(
            1, desde=start_date, hasta=end_date, limit=10, offset=0
        )

        expected_url = f"{BCRAConnector.BASE_URL}/estadisticas/v4.0/Monetarias/1"
        expected_params = {
            "Desde": "2024-03-01",
            "Hasta": "2024-03-05",
            "Limit": 10,
            "Offset": 0,
        }
        mock_get.assert_called_once_with(
            expected_url, params=expected_params, verify=False, timeout=ANY
        )

        assert isinstance(response, DatosVariableResponse)
        assert response.status == 200
        assert response.metadata.resultset.count == 2
        assert response.metadata.resultset.offset == 0
        assert response.metadata.resultset.limit == 10
        assert len(response.results) == 1
        dv = response.results[0]
        assert isinstance(dv, DatosVariable)
        assert dv.idVariable == 1
        assert len(dv.detalle) == 2
        assert dv.detalle[1].fecha == date(2024, 3, 5)
        assert dv.detalle[1].valor == 100.0

    def test_get_datos_variable_invalid_dates_v3(
        self, connector: BCRAConnector
    ) -> None:
        """Test handling of invalid date ranges (v4.0)."""
        with pytest.raises(
            ValueError,
            match="'desde' date must be earlier than or equal to 'hasta' date",
        ):
            connector.get_datos_variable(1, datetime(2024, 3, 5), datetime(2024, 3, 1))

    def test_get_datos_variable_invalid_limit_offset_v3(
        self, connector: BCRAConnector
    ) -> None:
        """Test validation for limit and offset in get_datos_variable (v4.0)."""
        valid_date = datetime(2024, 1, 1)
        with pytest.raises(ValueError, match="Limit must be between 10 and 3000"):
            connector.get_datos_variable(1, desde=valid_date, limit=5)
        with pytest.raises(ValueError, match="Limit must be between 10 and 3000"):
            connector.get_datos_variable(1, desde=valid_date, limit=3001)
        with pytest.raises(ValueError, match="Offset must be non-negative"):
            connector.get_datos_variable(1, desde=valid_date, offset=-1)
        try:
            connector.get_datos_variable(1, desde=valid_date, limit=10, offset=0)
        except ValueError:
            pytest.fail("Valid limit/offset raised ValueError unexpectedly.")

    @patch("bcra_connector.bcra_connector.BCRAConnector.get_datos_variable")
    def test_get_latest_value_success_v3(
        self, mock_get_datos_variable: Mock, connector: BCRAConnector
    ) -> None:
        """Test successful retrieval of latest value (using v4.0)."""
        mock_response_data = DatosVariableResponse(
            status=200,
            metadata=Mock(resultset=Mock(count=3, offset=0, limit=10)),
            results=[
                DatosVariable(
                    idVariable=1,
                    detalle=[
                        DetalleMonetaria(fecha=date(2024, 3, 3), valor=95.0),
                        DetalleMonetaria(fecha=date(2024, 3, 5), valor=100.0),
                        DetalleMonetaria(fecha=date(2024, 3, 4), valor=97.5),
                    ],
                )
            ],
        )
        mock_get_datos_variable.return_value = mock_response_data

        result = connector.get_latest_value(1)

        mock_get_datos_variable.assert_any_call(1, limit=10)

        assert isinstance(result, DetalleMonetaria)
        assert result.fecha == date(2024, 3, 5)
        assert result.valor == 100.0

    @patch("bcra_connector.bcra_connector.BCRAConnector.get_datos_variable")
    def test_get_latest_value_no_data_v3(
        self, mock_get_datos_variable: Mock, connector: BCRAConnector
    ) -> None:
        """Test handling of no data for latest value (using v4.0)."""
        mock_empty_response = DatosVariableResponse(
            status=200,
            metadata=Mock(resultset=Mock(count=0, offset=0, limit=10)),
            results=[],
        )
        mock_get_datos_variable.side_effect = [mock_empty_response, mock_empty_response]

        with pytest.raises(BCRAApiError, match="No data available for variable 1"):
            connector.get_latest_value(1)

        assert mock_get_datos_variable.call_count == 2
        mock_get_datos_variable.assert_any_call(1, limit=10)
        mock_get_datos_variable.assert_any_call(1, desde=ANY, hasta=ANY, limit=ANY)

    @patch("bcra_connector.bcra_connector.BCRAConnector.get_datos_variable")
    def test_get_latest_value_fallback_success(
        self, mock_get_datos_variable: Mock, connector: BCRAConnector
    ) -> None:
        """Test fallback scenario where first query is empty but 30-day query succeeds."""
        # First call with limit=10 returns empty results
        mock_empty_response = DatosVariableResponse(
            status=200,
            metadata=Mock(resultset=Mock(count=0, offset=0, limit=10)),
            results=[],
        )
        # Second call (30-day fallback) returns data
        mock_fallback_response = DatosVariableResponse(
            status=200,
            metadata=Mock(resultset=Mock(count=2, offset=0, limit=30)),
            results=[
                DatosVariable(
                    idVariable=1,
                    detalle=[
                        DetalleMonetaria(fecha=date(2024, 2, 1), valor=50.0),
                        DetalleMonetaria(fecha=date(2024, 2, 15), valor=75.0),
                    ],
                )
            ],
        )
        mock_get_datos_variable.side_effect = [
            mock_empty_response,
            mock_fallback_response,
        ]

        result = connector.get_latest_value(1)

        # Verify both calls were made
        assert mock_get_datos_variable.call_count == 2
        mock_get_datos_variable.assert_any_call(1, limit=10)
        mock_get_datos_variable.assert_any_call(1, desde=ANY, hasta=ANY, limit=ANY)

        # Verify we got the latest from fallback data
        assert isinstance(result, DetalleMonetaria)
        assert result.fecha == date(2024, 2, 15)
        assert result.valor == 75.0

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_entidades_success(
        self,
        mock_get: Mock,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
        connector: BCRAConnector,
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
        result: List[Entidad] = connector.get_entidades()

        mock_get.assert_called_once_with(
            f"{BCRAConnector.BASE_URL}/cheques/v1.0/entidades",
            params=None,
            verify=False,
            timeout=ANY,
        )
        assert len(result) == 2
        assert all(isinstance(entity, Entidad) for entity in result)
        assert result[0].codigo_entidad == 11

    @patch("bcra_connector.bcra_connector.requests.Session.get")
    def test_get_cheque_denunciado_success(
        self,
        mock_get: Mock,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
        connector: BCRAConnector,
    ) -> None:
        """Test successful retrieval of reported check information."""
        mock_data_dict: Dict[str, Any] = {
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
        mock_get.return_value = mock_api_response(mock_data_dict, 200)
        result: Cheque = connector.get_cheque_denunciado(11, 20377516)

        mock_get.assert_called_once_with(
            f"{BCRAConnector.BASE_URL}/cheques/v1.0/denunciados/11/20377516",
            params=None,
            verify=False,
            timeout=ANY,
        )
        assert isinstance(result, Cheque)
        assert result.numero_cheque == 20377516

    def test_error_handling_timeout(self, connector: BCRAConnector) -> None:
        """Test timeout error handling."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.side_effect = Timeout("Request timed out")
            with pytest.raises(BCRAApiError, match="Request timed out"):
                connector.get_principales_variables()

    def test_error_handling_connection_error(self, connector: BCRAConnector) -> None:
        """Test connection error handling."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")
            with pytest.raises(
                BCRAApiError, match="API request failed: Connection error"
            ):
                connector.get_principales_variables()

    def test_error_handling_http_error_generic(
        self,
        connector: BCRAConnector,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
    ) -> None:
        """Test generic HTTP error handling (non-404)."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_resp = mock_api_response({"errorMessages": ["Server Issue"]}, 500)
            mock_get.return_value = mock_resp

            with pytest.raises(BCRAApiError, match="HTTP 500"):
                connector.get_principales_variables()

    def test_error_handling_http_404_error(
        self,
        connector: BCRAConnector,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
    ) -> None:
        """Test 404 HTTP error handling from _make_request."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            variable_id_for_test = 99999
            mocked_api_url_path = f"estadisticas/v4.0/Monetarias/{variable_id_for_test}"
            full_mocked_url = f"{BCRAConnector.BASE_URL}/{mocked_api_url_path}"
            api_error_content_message = "Recurso Especifico No Encontrado"

            mock_resp = mock_api_response(
                {"errorMessages": [api_error_content_message]}, 404
            )
            mock_resp.url = full_mocked_url

            mock_get.return_value = mock_resp

            expected_match_pattern = r"Resource not found \(404\)"

            with pytest.raises(BCRAApiError, match=expected_match_pattern) as exc_info:
                connector.get_datos_variable(variable_id_for_test)

            assert full_mocked_url in str(exc_info.value)
            assert api_error_content_message in str(exc_info.value)
            assert "HTTP 404" in str(exc_info.value)

    def test_rate_limiting(self, connector: BCRAConnector) -> None:
        """Test rate limiting functionality."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.return_value = Mock(
                json=lambda: {"results": []},
                status_code=200,
                raise_for_status=lambda: None,
            )

            for _ in range(connector.rate_limiter.config.burst):
                delay = connector.rate_limiter.acquire()
                assert delay == 0.0

            delay_needed = connector.rate_limiter.acquire()
            assert delay_needed > 0.0
            assert (
                connector.rate_limiter.current_usage
                == connector.rate_limiter.config.burst + 1
            )

    @pytest.mark.parametrize(
        "response_code,error_messages,expected_match",
        [
            (400, ["Bad Request"], "HTTP 400"),
            (404, ["Not Found"], "Resource not found"),
            (500, ["Internal Server Error"], "HTTP 500"),
            (429, ["Too Many Requests"], "HTTP 429"),
        ],
    )
    def test_error_responses_v3(
        self,
        connector: BCRAConnector,
        response_code: int,
        error_messages: List[str],
        expected_match: str,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
    ) -> None:
        """Test handling of various error responses using a v4.0 endpoint."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_response_obj: Mock = mock_api_response(
                {"errorMessages": error_messages},
                response_code,
            )
            if response_code >= 400:
                mock_response_obj.raise_for_status.side_effect = HTTPError(
                    response=mock_response_obj
                )

            mock_get.return_value = mock_response_obj

            with pytest.raises(BCRAApiError) as exc_info:
                connector.get_principales_variables()

            assert expected_match in str(exc_info.value)
            if error_messages:
                assert all(msg in str(exc_info.value) for msg in error_messages)

    def test_retry_mechanism(
        self,
        connector: BCRAConnector,
        mock_api_response: Callable[[Dict[str, Any], int], Mock],
    ) -> None:
        """Test retry mechanism for failed requests."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            final_response = mock_api_response({"results": []}, 200)
            mock_get.side_effect = [
                ConnectionError("First attempt failed"),
                Timeout("Second attempt failed"),
                final_response,
            ]

            result: List[PrincipalesVariables] = connector.get_principales_variables()
            assert result == []
            assert mock_get.call_count == 3
