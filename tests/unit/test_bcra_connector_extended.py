"""
Extended test suite for BCRAConnector class to achieve 100% coverage.
"""

import json
from datetime import date
from typing import Any, Callable, Dict
from unittest.mock import Mock, patch

import numpy as np
import pytest
from requests.exceptions import ConnectionError, HTTPError, RequestException

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Cheque, Entidad
from bcra_connector.estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha
from bcra_connector.principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
from bcra_connector.rate_limiter import RateLimitConfig


class TestBCRAConnectorExtended:
    """Extended test cases for BCRAConnector class to cover edge cases."""

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
            # If data is a dict/list, json() returns it. If string (bad json), side_effect raises JSONDecodeError
            if isinstance(data, (dict, list)):
                response.json.return_value = data
            return response

        return _create_response

    # --- _make_request edge cases ---
    def test_make_request_http_error_json_decode_fail(self, connector: BCRAConnector):
        """Test HTTP error where response body is not valid JSON."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 500
            mock_resp.url = "http://test.url"
            mock_resp.reason = "Internal Server Error"
            mock_resp.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_resp.raise_for_status.side_effect = HTTPError(response=mock_resp)
            mock_get.return_value = mock_resp

            with pytest.raises(BCRAApiError) as exc_info:
                connector._make_request("test")
            assert "HTTP 500" in str(exc_info.value)
            assert "Internal Server Error" in str(exc_info.value)

    def test_make_request_http_error_dict_no_error_message(
        self, connector: BCRAConnector
    ):
        """Test HTTP error where response is JSON dict but has no errorMessages key."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 400
            mock_resp.url = "http://test.url"
            mock_resp.json.return_value = {"some_other_key": "val"}
            mock_resp.raise_for_status.side_effect = HTTPError(response=mock_resp)
            mock_get.return_value = mock_resp

            with pytest.raises(BCRAApiError) as exc_info:
                connector._make_request("test")
            assert "HTTP 400" in str(exc_info.value)
            assert "{'some_other_key': 'val'}" in str(exc_info.value)

    def test_make_request_ssl_error(self, connector: BCRAConnector):
        """Test handling of SSL errors."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.side_effect = ConnectionError("SSL: CERTIFICATE_VERIFY_FAILED")
            with pytest.raises(BCRAApiError, match="SSL issue"):
                connector._make_request("test")

    def test_make_request_max_retries_exceeded_generic_exception(
        self, connector: BCRAConnector
    ):
        """Test max retries exceeded for generic RequestException."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_get.side_effect = RequestException("Generic Error")
            with pytest.raises(
                BCRAApiError, match="API request failed after 3 attempts"
            ):
                connector._make_request("test")
            assert mock_get.call_count == 3

    def test_make_request_max_retries_exceeded_loop_end(self, connector: BCRAConnector):
        """Test falling through the retry loop without raising specific exception (unlikely path but covered)."""
        # This effectively tests the raise BCRAApiError at the very end of _make_request
        # We need to simulate a case where the loop finishes but doesn't return.
        # Actually, the loop always catches exceptions or returns.
        # The only way to reach end is if range(MAX_RETRIES) is 0, but it's hardcoded to 3.
        # Or if we mock MAX_RETRIES to 0.
        connector.MAX_RETRIES = 0
        with pytest.raises(BCRAApiError, match="Maximum retry attempts"):
            connector._make_request("test")
        connector.MAX_RETRIES = 3  # Reset

    def test_make_request_json_decode_error_on_success(self, connector: BCRAConnector):
        """Test invalid JSON response on successful status code."""
        with patch("bcra_connector.bcra_connector.requests.Session.get") as mock_get:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.side_effect = json.JSONDecodeError("Fail", "", 0)
            mock_get.return_value = mock_resp

            with pytest.raises(BCRAApiError, match="Invalid JSON response"):
                connector._make_request("test")

    # --- monetarias.list() edge cases ---
    def test_monetarias_list_invalid_results_format(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", return_value={"results": "not-a-list"}
        ):
            with pytest.raises(BCRAApiError, match="Unexpected response format"):
                connector.monetarias.list()

    def test_monetarias_list_parsing_error(self, connector: BCRAConnector):
        # One valid, one invalid item
        data = {
            "results": [
                {
                    "idVariable": 1,
                    "descripcion": "Valid",
                    "categoria": "C",
                },
                {
                    "idVariable": 2
                },  # Missing fields is OK in v4.0 since most are optional
            ]
        }
        with patch.object(connector._http, "request", return_value=data):
            # Should parse both successfully in v4.0
            res = connector.monetarias.list()
            assert len(res) == 2

    def test_monetarias_list_all_parsing_failed(self, connector: BCRAConnector):
        data = {
            "results": [{"invalid": "data"}]
        }  # Will raise KeyError/ValueError during from_dict
        with patch.object(connector._http, "request", return_value=data):
            # Logs error but returns empty list? or raises?
            # Code says log error if results existed but parsing failed. Returns empty list.
            res = connector.monetarias.list()
            assert res == []

    def test_monetarias_list_no_valid_variables(self, connector: BCRAConnector):
        with patch.object(connector._http, "request", return_value={"results": []}):
            res = connector.monetarias.list()
            assert res == []

    def test_monetarias_list_exception(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", side_effect=Exception("Unexpected")
        ):
            with pytest.raises(
                BCRAApiError, match="Error fetching principal variables"
            ):
                connector.monetarias.list()

    # --- monetarias.series() edge cases ---
    def test_monetarias_series_parsing_error(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", return_value={"results": "bad-structure"}
        ):
            with pytest.raises(BCRAApiError, match="Error parsing response"):
                connector.monetarias.series(1)

    def test_monetarias_series_unexpected_exception(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", side_effect=Exception("Unexpected")
        ):
            with pytest.raises(BCRAApiError, match="Unexpected error fetching data"):
                connector.monetarias.series(1)

    def test_monetarias_series_api_error_pass_through(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", side_effect=BCRAApiError("API Error")
        ):
            with pytest.raises(BCRAApiError, match="API Error"):
                connector.monetarias.series(1)

    # --- get_entidades edge cases ---
    def test_get_entidades_invalid_format(self, connector: BCRAConnector):
        with patch.object(connector._http, "request", return_value={"no-results": []}):
            with pytest.raises(BCRAApiError, match="Invalid response format"):
                connector.cheques.entities()

    def test_get_entidades_parsing_error(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", return_value={"results": [{"bad": "data"}]}
        ):
            with pytest.raises(BCRAApiError, match="Unexpected response format"):
                connector.cheques.entities()

    def test_get_entidades_pass_bcra_error(self, connector: BCRAConnector):
        with patch.object(connector._http, "request", side_effect=BCRAApiError("Fail")):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.cheques.entities()

    def test_get_entidades_unexpected_error(self, connector: BCRAConnector):
        with patch.object(connector._http, "request", side_effect=Exception("Fail")):
            with pytest.raises(BCRAApiError, match="Error fetching financial entities"):
                connector.cheques.entities()

    # --- get_cheque_denunciado edge cases ---
    def test_get_cheque_denunciado_invalid_format(self, connector: BCRAConnector):
        with patch.object(
            connector._http, "request", return_value={"results": "not-a-dict"}
        ):
            with pytest.raises(BCRAApiError, match="Invalid response format"):
                connector.cheques.reported(1, 123)

    def test_get_cheque_denunciado_parsing_error(self, connector: BCRAConnector):
        # Missing keys
        with patch.object(connector._http, "request", return_value={"results": {}}):
            with pytest.raises(BCRAApiError, match="Unexpected response format"):
                connector.cheques.reported(1, 123)

    def test_get_cheque_denunciado_pass_bcra_error(self, connector: BCRAConnector):
        with patch.object(connector._http, "request", side_effect=BCRAApiError("Fail")):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.cheques.reported(1, 123)

    def test_get_cheque_denunciado_unexpected_error(self, connector: BCRAConnector):
        with patch.object(connector._http, "request", side_effect=Exception("Fail")):
            with pytest.raises(BCRAApiError, match="Error fetching reported check"):
                connector.cheques.reported(1, 123)

    # --- get_divisas edge cases ---
    def test_get_divisas_success(self, connector: BCRAConnector):
        data = {"results": [{"codigo": "USD", "denominacion": "Dolar USA"}]}
        with patch.object(connector, "_make_request", return_value=data):
            res = connector.get_divisas()
            assert len(res) == 1
            assert res[0].codigo == "USD"

    def test_get_divisas_invalid_format(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", return_value={"results": "bad"}):
            with pytest.raises(BCRAApiError, match="Invalid response format"):
                connector.get_divisas()

    def test_get_divisas_parsing_error(self, connector: BCRAConnector):
        with patch.object(
            connector, "_make_request", return_value={"results": [{"bad": "data"}]}
        ):
            with pytest.raises(BCRAApiError, match="Unexpected response format"):
                connector.get_divisas()

    def test_get_divisas_pass_bcra_error(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", side_effect=BCRAApiError("Fail")):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.get_divisas()

    def test_get_divisas_unexpected_error(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", side_effect=Exception("Fail")):
            with pytest.raises(BCRAApiError, match="Error fetching currencies"):
                connector.get_divisas()

    # --- get_cotizaciones edge cases ---
    def test_get_cotizaciones_success(self, connector: BCRAConnector):
        data = {
            "results": {
                "fecha": "2024-01-01",
                "detalle": [
                    {
                        "codigoMoneda": "USD",
                        "tipoCotizacion": 100.0,
                        "tipoPase": 0.0,
                        "descripcion": "Dollar",
                    }
                ],
            }
        }
        with patch.object(connector, "_make_request", return_value=data) as mock_req:
            res = connector.get_cotizaciones("2024-01-01")
            assert res.fecha == date(2024, 1, 1)
            mock_req.assert_called_with(
                "estadisticascambiarias/v1.0/Cotizaciones", {"fecha": "2024-01-01"}
            )

    def test_get_cotizaciones_invalid_format(self, connector: BCRAConnector):
        with patch.object(
            connector, "_make_request", return_value={"results": []}
        ):  # Expected dict
            with pytest.raises(BCRAApiError, match="Invalid response format"):
                connector.get_cotizaciones()

    def test_get_cotizaciones_parsing_error(self, connector: BCRAConnector):
        with patch.object(
            connector, "_make_request", return_value={"results": {"bad": "data"}}
        ):
            with pytest.raises(BCRAApiError, match="Unexpected response format"):
                connector.get_cotizaciones()

    def test_get_cotizaciones_pass_bcra_error(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", side_effect=BCRAApiError("Fail")):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.get_cotizaciones()

    def test_get_cotizaciones_unexpected_error(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", side_effect=Exception("Fail")):
            with pytest.raises(BCRAApiError, match="Error fetching quotations"):
                connector.get_cotizaciones()

    # --- get_evolucion_moneda edge cases ---
    def test_get_evolucion_moneda_success(self, connector: BCRAConnector):
        data = {"results": [{"fecha": "2024-01-01", "detalle": []}]}
        with patch.object(connector, "_make_request", return_value=data):
            res = connector.get_evolucion_moneda("USD")
            assert len(res) == 1

    def test_get_evolucion_moneda_invalid_params(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="Limit must be between"):
            connector.get_evolucion_moneda("USD", limit=5)
        with pytest.raises(ValueError, match="Offset must be non-negative"):
            connector.get_evolucion_moneda("USD", offset=-1)

    def test_get_evolucion_moneda_invalid_format(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", return_value={"results": "bad"}):
            with pytest.raises(BCRAApiError, match="Invalid response format"):
                connector.get_evolucion_moneda("USD")

    def test_get_evolucion_moneda_parsing_error(self, connector: BCRAConnector):
        with patch.object(
            connector, "_make_request", return_value={"results": [{"bad": "data"}]}
        ):
            with pytest.raises(BCRAApiError, match="Unexpected response format"):
                connector.get_evolucion_moneda("USD")

    def test_get_evolucion_moneda_pass_bcra_error(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", side_effect=BCRAApiError("Fail")):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.get_evolucion_moneda("USD")

    def test_get_evolucion_moneda_unexpected_error(self, connector: BCRAConnector):
        with patch.object(connector, "_make_request", side_effect=Exception("Fail")):
            with pytest.raises(BCRAApiError, match="Error fetching evolution"):
                connector.get_evolucion_moneda("USD")

    # --- helper methods ---
    def test_monetarias_find_found(self, connector: BCRAConnector):
        vars_list = [
            PrincipalesVariables(
                idVariable=1,
                descripcion="Reserva",
            )
        ]
        with patch.object(connector.monetarias, "list", return_value=vars_list):
            res = connector.monetarias.find("reserva")
            assert res.idVariable == 1

    def test_monetarias_find_not_found(self, connector: BCRAConnector):
        vars_list = [
            PrincipalesVariables(
                idVariable=1,
                descripcion="Base",
            )
        ]
        with patch.object(connector.monetarias, "list", return_value=vars_list):
            res = connector.monetarias.find("reserva")
            assert res is None

    def test_monetarias_find_error_propagates(self, connector: BCRAConnector):
        """An API failure must not be reported as 'variable not found'."""
        with patch.object(
            connector.monetarias, "list", side_effect=BCRAApiError("Fail")
        ):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.monetarias.find("any")
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.monetarias.history("any")

    def test_monetarias_find_prefers_exact_match(self, connector: BCRAConnector):
        vars_list = [
            PrincipalesVariables(idVariable=1, descripcion="Reservas en oro"),
            PrincipalesVariables(idVariable=2, descripcion="Reservas"),
        ]
        with patch.object(connector.monetarias, "list", return_value=vars_list):
            assert connector.monetarias.find(" reservas ").idVariable == 2

    def test_monetarias_find_warns_on_ambiguous_match(
        self, connector: BCRAConnector, caplog: pytest.LogCaptureFixture
    ):
        vars_list = [
            PrincipalesVariables(idVariable=7, descripcion="Tasa BADLAR"),
            PrincipalesVariables(idVariable=8, descripcion="Tasa TAMAR"),
            PrincipalesVariables(idVariable=9, descripcion="Base monetaria"),
        ]
        with patch.object(connector.monetarias, "list", return_value=vars_list):
            with caplog.at_level("WARNING", logger="bcra_connector"):
                res = connector.monetarias.find("tasa")

        assert res.idVariable == 7  # first match, as before
        warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
        assert len(warnings) == 1
        assert "2 variables match 'tasa'" in warnings[0]
        assert "8" in warnings[0] and "Tasa TAMAR" in warnings[0]

    def test_monetarias_find_single_match_no_warning(
        self, connector: BCRAConnector, caplog: pytest.LogCaptureFixture
    ):
        vars_list = [PrincipalesVariables(idVariable=1, descripcion="Base monetaria")]
        with patch.object(connector.monetarias, "list", return_value=vars_list):
            with caplog.at_level("WARNING", logger="bcra_connector"):
                connector.monetarias.find("base")
        assert not [r for r in caplog.records if r.levelname == "WARNING"]

    def test_monetarias_history_methods(self, connector: BCRAConnector):
        # We must mock find() first because history() calls it.
        mock_var = PrincipalesVariables(
            idVariable=1,
            descripcion="Var",
        )

        # Scenario 1: Variable found, but days invalid
        with patch.object(connector.monetarias, "find", return_value=mock_var):
            with pytest.raises(ValueError, match="positive"):
                connector.monetarias.history("Var", days=-1)

        # Scenario 2: Variable not found
        with patch.object(connector.monetarias, "find", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                connector.monetarias.history("Missing")

        # Scenario 3: Success
        with patch.object(connector.monetarias, "find", return_value=mock_var):
            with patch.object(connector.monetarias, "series") as mock_get_datos:
                mock_get_datos.return_value = DatosVariableResponse(
                    status=200,
                    metadata=Mock(),
                    results=[
                        DatosVariable(
                            idVariable=1,
                            detalle=[DetalleMonetaria(fecha=date.today(), valor=10.0)],
                        )
                    ],
                )
                res = connector.monetarias.history("Var", days=10)
                assert len(res) == 1
                mock_get_datos.assert_called_once()

    def test_get_currency_evolution_helper(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="positive"):
            connector.get_currency_evolution("USD", days=-1)

        # Explicit limit: a single page through get_evolucion_moneda.
        with patch.object(
            connector, "get_evolucion_moneda", return_value=[]
        ) as mock_get:
            connector.get_currency_evolution("USD", days=10, limit=100)
            mock_get.assert_called_once()

        # Default: the whole range, page by page.
        with patch.object(
            connector, "_fetch_evolucion_moneda_page", return_value=([], 0)
        ) as mock_page:
            connector.get_currency_evolution("USD", days=10)
            mock_page.assert_called_once()

        with pytest.raises(ValueError, match="non-negative"):
            connector.get_currency_evolution("USD", days=10, offset=-1)

    def test_check_denunciado_flow(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="positive"):
            connector.cheques.is_reported("Bank", -1)

        with patch.object(
            connector.cheques, "entities", side_effect=BCRAApiError("Fail")
        ):
            with pytest.raises(BCRAApiError, match="Fail"):
                connector.cheques.is_reported("Bank", 123)

        entidades = [Entidad(codigo_entidad=1, denominacion="BankOfTest")]
        with patch.object(connector.cheques, "entities", return_value=entidades):
            # Not found entity
            with pytest.raises(ValueError, match="not found"):
                connector.cheques.is_reported("Other", 123)

            # Found entity, check reported
            # Mock Cheque correctly without extra args
            check_ok = Cheque(20, True, date.today(), "BankOfTest", [])
            with patch.object(connector.cheques, "reported", return_value=check_ok):
                assert connector.cheques.is_reported("BankOfTest", 123) is True

            # Found entity, check NOT reported: the API answers 200 + False
            check_clean = Cheque(20, False, date.today(), "BankOfTest", [])
            with patch.object(connector.cheques, "reported", return_value=check_clean):
                assert connector.cheques.is_reported("BankOfTest", 123) is False

            # Found entity, other api error
            with patch.object(
                connector.cheques,
                "reported",
                side_effect=BCRAApiError("500 Error"),
            ):
                with pytest.raises(BCRAApiError, match="500 Error"):
                    connector.cheques.is_reported("BankOfTest", 123)

            # unexpected error
            with patch.object(
                connector.cheques, "reported", side_effect=Exception("Unexp")
            ):
                with pytest.raises(BCRAApiError, match="Unexpected error during check"):
                    connector.cheques.is_reported("BankOfTest", 123)

    def test_get_latest_quotations_flow(self, connector: BCRAConnector):
        # API Error
        with patch.object(
            connector, "get_cotizaciones", side_effect=BCRAApiError("Fail")
        ):
            with pytest.raises(BCRAApiError):
                connector.get_latest_quotations()

        # Empty/None
        with patch.object(
            connector,
            "get_cotizaciones",
            return_value=CotizacionFecha(fecha=date.today(), detalle=[]),
        ):
            res = connector.get_latest_quotations()
            assert res == {}

        # Success - CotizacionDetalle has required fields
        data = CotizacionFecha(
            fecha=date.today(),
            detalle=[
                CotizacionDetalle(
                    codigo_moneda="USD",
                    tipo_cotizacion=100.0,
                    descripcion="Dollar",
                    tipo_pase=0.0,
                )
            ],
        )
        with patch.object(connector, "get_cotizaciones", return_value=data):
            res = connector.get_latest_quotations()
            assert res["USD"] == 100.0

    def test_get_currency_pair_evolution_flow(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="positive"):
            connector.get_currency_pair_evolution("USD", "EUR", days=-1)

        # API Error
        with patch.object(
            connector, "get_currency_evolution", side_effect=BCRAApiError("Fail")
        ):
            with pytest.raises(BCRAApiError):
                connector.get_currency_pair_evolution("USD", "EUR")

        # Success logic with division by zero avoidance and alignment
        d1 = date(2024, 1, 1)
        d2 = date(2024, 1, 2)

        def mock_get_ev(code, *args, **kwargs):
            assert code == "EUR"  # USD/EUR only needs the EUR series
            return [
                CotizacionFecha(
                    fecha=d1,
                    detalle=[
                        CotizacionDetalle(
                            codigo_moneda="EUR",
                            descripcion="E",
                            tipo_pase=2.0,
                            tipo_cotizacion=200.0,
                        )
                    ],
                ),
                CotizacionFecha(
                    fecha=d2,
                    detalle=[
                        CotizacionDetalle(
                            codigo_moneda="EUR",
                            descripcion="E",
                            tipo_pase=0.0,
                            tipo_cotizacion=0.0,
                        )
                    ],
                ),  # Zero val
            ]

        with patch.object(connector, "get_currency_evolution", side_effect=mock_get_ev):
            res = connector.get_currency_pair_evolution("USD", "EUR")
            # d1: 1 USD = 1 / 2.0 EUR
            # d2: EUR 0 -> skipped
            assert len(res) == 1
            assert res[0]["tasa"] == 0.5

        # Helper _get_cotizacion_detalle errors
        # Let's force a ValueError by returning CotizacionFecha without the expected currency
        def mock_get_ev_missing(code, *args, **kwargs):
            return [CotizacionFecha(fecha=d1, detalle=[])]  # No details

        with patch.object(
            connector, "get_currency_evolution", side_effect=mock_get_ev_missing
        ):
            res = connector.get_currency_pair_evolution("USD", "EUR")
            assert res == []

    def test_get_variable_correlation_flow(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="greater than 1"):
            connector.get_variable_correlation("A", "B", days=1)

        # API Error
        with patch.object(
            connector.monetarias, "history", side_effect=BCRAApiError("Fail")
        ):
            with pytest.raises(BCRAApiError):
                connector.get_variable_correlation("A", "B")

        # Insufficient data (None returned)
        with patch.object(connector.monetarias, "history", return_value=[]):
            assert np.isnan(connector.get_variable_correlation("A", "B"))

        # Insufficient unique dates
        d1 = DetalleMonetaria(fecha=date(2024, 1, 1), valor=10.0)
        with patch.object(connector.monetarias, "history", return_value=[d1, d1]):
            # Same date twice (set len < 2)
            assert np.isnan(connector.get_variable_correlation("A", "B"))

        # Safe mock for success
        d1 = DetalleMonetaria(fecha=date(2024, 1, 1), valor=10.0)
        d2 = DetalleMonetaria(fecha=date(2024, 1, 2), valor=20.0)
        d3 = DetalleMonetaria(fecha=date(2024, 1, 3), valor=30.0)

        with patch.object(
            connector.monetarias, "history", side_effect=[[d1, d2, d3], [d1, d2, d3]]
        ):  # Perfect correlation
            corr = connector.get_variable_correlation("A", "B")
            assert corr == pytest.approx(1.0)  # Check floating point equality

        # Constants => NaN
        dc1 = DetalleMonetaria(fecha=date(2024, 1, 1), valor=10.0)
        dc2 = DetalleMonetaria(fecha=date(2024, 1, 2), valor=10.0)
        with patch.object(
            connector.monetarias, "history", side_effect=[[dc1, dc2], [d1, d2]]
        ):
            assert np.isnan(connector.get_variable_correlation("A", "B"))

    def test_init_numeric_timeout(self):
        c = BCRAConnector(timeout=10.0)
        # TimeoutConfig.from_total(10.0) -> connect=1.0, read=9.0
        assert c.timeout.connect == 1.0
        assert c.timeout.read == 9.0

    def test_make_request_rate_limit_delay(self, connector: BCRAConnector):
        with patch.object(connector.rate_limiter, "acquire", side_effect=[0.1, 0.0]):
            with patch("bcra_connector._http.time.sleep") as mock_sleep:
                with patch.object(connector._http, "session") as mock_session:
                    mock_session.get.return_value = Mock(
                        status_code=200, raise_for_status=lambda: None, json=lambda: {}
                    )
                    connector._make_request("test")
                    mock_sleep.assert_called_with(0.1)

    def test_get_cotizacion_detalle_not_found(self, connector: BCRAConnector):
        # type_passe and tipo_cotizacion are required args
        cf = CotizacionFecha(
            date(2024, 1, 1), [CotizacionDetalle("USD", "D", 100.0, 100.0)]
        )
        with pytest.raises(ValueError, match="not found in cotizacion"):
            connector._get_cotizacion_detalle(cf, "EUR")

    def test_get_cotizacion_detalle_empty(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="Invalid or empty"):
            connector._get_cotizacion_detalle(None, "USD")

    def test_get_variable_correlation_nan(self, connector: BCRAConnector):
        d1 = DetalleMonetaria(fecha=date(2024, 1, 1), valor=10.0)
        d2 = DetalleMonetaria(fecha=date(2024, 1, 2), valor=20.0)
        d3 = DetalleMonetaria(fecha=date(2024, 1, 3), valor=30.0)

        with patch.object(
            connector.monetarias, "history", side_effect=[[d1, d2, d3], [d1, d2, d3]]
        ):
            with patch(
                "numpy.corrcoef",
                return_value=np.array([[1.0, np.nan], [np.nan, 1.0]]),
            ):
                res = connector.get_variable_correlation("A", "B")
                assert np.isnan(res)

        # Pearson error? handled by constant check usually, but code has try-catch.

    def test_generate_variable_report_flow(self, connector: BCRAConnector):
        with pytest.raises(ValueError, match="positive"):
            connector.generate_variable_report("A", days=-1)

        with patch.object(connector.monetarias, "find", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                connector.generate_variable_report("Missing")

        mock_var = PrincipalesVariables(idVariable=1, descripcion="Desc")
        with patch.object(connector.monetarias, "find", return_value=mock_var):

            # API Error
            with patch.object(
                connector.monetarias, "history", side_effect=BCRAApiError("Fail")
            ):
                with pytest.raises(BCRAApiError):
                    connector.generate_variable_report("A")

            # No data
            with patch.object(connector.monetarias, "history", return_value=[]):
                rep = connector.generate_variable_report("A")
                assert "error" in rep

            # Success
            d1 = DetalleMonetaria(fecha=date(2024, 1, 1), valor=100.0)
            d2 = DetalleMonetaria(fecha=date(2024, 1, 2), valor=200.0)
            with patch.object(connector.monetarias, "history", return_value=[d1, d2]):
                rep = connector.generate_variable_report("A")
                assert rep["min_value"] == 100.0
                assert rep["max_value"] == 200.0
                assert rep["percent_change"] == 100.0

    def test_generate_variable_report_descending_history(
        self, connector: BCRAConnector
    ):
        """The API returns series newest-first; the report must not depend on it."""
        mock_var = PrincipalesVariables(idVariable=1, descripcion="Desc")
        newest_first = [
            DetalleMonetaria(fecha=date(2024, 1, 3), valor=300.0),
            DetalleMonetaria(fecha=date(2024, 1, 2), valor=200.0),
            DetalleMonetaria(fecha=date(2024, 1, 1), valor=100.0),
        ]
        with patch.object(connector.monetarias, "find", return_value=mock_var):
            with patch.object(
                connector.monetarias, "history", return_value=newest_first
            ):
                rep = connector.generate_variable_report("A")

        assert rep["start_date"] == "2024-01-01"
        assert rep["end_date"] == "2024-01-03"
        assert rep["latest_date"] == "2024-01-03"
        assert rep["latest_value"] == 300.0
        assert rep["percent_change"] == 200.0
