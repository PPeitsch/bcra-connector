"""
Unit tests for the Central de Deudores client (``connector.deudores``).
Tests: debts, historical, rejected_checks.
"""

from unittest.mock import MagicMock, patch

import pytest

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector._http import HttpClient


class TestGetDeudas:
    """Tests for get_deudas method."""

    @patch.object(HttpClient, "request")
    def test_get_deudas_success(self, mock_request: MagicMock) -> None:
        """Test successful deudas retrieval."""
        mock_request.return_value = {
            "status": 200,
            "results": {
                "identificacion": 20123456789,
                "denominacion": "JUAN PEREZ",
                "periodos": [
                    {
                        "periodo": "202403",
                        "entidades": [
                            {
                                "entidad": "BANCO DE LA NACION ARGENTINA",
                                "situacion": 1,
                                "monto": 35.0,
                                "enRevision": False,
                                "procesoJud": False,
                            }
                        ],
                    }
                ],
            },
        }

        connector = BCRAConnector()
        result = connector.deudores.debts("20123456789")

        assert result.identificacion == 20123456789
        assert result.denominacion == "JUAN PEREZ"
        assert len(result.periodos) == 1
        assert result.periodos[0].entidades[0].situacion == 1

    @patch.object(HttpClient, "request")
    def test_get_deudas_strips_formatting(self, mock_request: MagicMock) -> None:
        """Test that CUIT formatting is stripped."""
        mock_request.return_value = {
            "status": 200,
            "results": {
                "identificacion": 20123456789,
                "denominacion": "TEST",
                "periodos": [],
            },
        }

        connector = BCRAConnector()
        connector.deudores.debts("20-12345678-9")

        mock_request.assert_called_once()
        call_args = mock_request.call_args[0][0]
        assert "20123456789" in call_args

    def test_get_deudas_invalid_length(self) -> None:
        """Test validation of identificacion length."""
        connector = BCRAConnector()
        with pytest.raises(ValueError, match="exactly 11 digits"):
            connector.deudores.debts("12345")

    def test_get_deudas_non_numeric(self) -> None:
        """Test validation of non-numeric identificacion."""
        connector = BCRAConnector()
        with pytest.raises(ValueError, match="exactly 11 digits"):
            connector.deudores.debts("2012345678A")

    @patch.object(HttpClient, "request")
    def test_get_deudas_invalid_response(self, mock_request: MagicMock) -> None:
        """Test handling of invalid API response."""
        mock_request.return_value = {"status": 200}

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Invalid response format"):
            connector.deudores.debts("20123456789")

    @patch.object(HttpClient, "request")
    def test_get_deudas_api_error(self, mock_request: MagicMock) -> None:
        """Test handling of API error."""
        mock_request.side_effect = BCRAApiError("API error")

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="API error"):
            connector.deudores.debts("20123456789")


class TestGetDeudasHistoricas:
    """Tests for get_deudas_historicas method."""

    @patch.object(HttpClient, "request")
    def test_get_deudas_historicas_success(self, mock_request: MagicMock) -> None:
        """Test successful historical deudas retrieval."""
        mock_request.return_value = {
            "status": 200,
            "results": {
                "identificacion": 30987654321,
                "denominacion": "EMPRESA SA",
                "periodos": [
                    {
                        "periodo": "202403",
                        "entidades": [
                            {"entidad": "BANCO A", "situacion": 1, "monto": 100.0}
                        ],
                    },
                    {
                        "periodo": "202402",
                        "entidades": [
                            {"entidad": "BANCO A", "situacion": 1, "monto": 150.0}
                        ],
                    },
                ],
            },
        }

        connector = BCRAConnector()
        result = connector.deudores.historical("30987654321")

        assert result.identificacion == 30987654321
        assert len(result.periodos) == 2

    def test_get_deudas_historicas_invalid_length(self) -> None:
        """Test validation of identificacion length."""
        connector = BCRAConnector()
        with pytest.raises(ValueError, match="exactly 11 digits"):
            connector.deudores.historical("123")


class TestGetChequesRechazados:
    """Tests for get_cheques_rechazados method."""

    @patch.object(HttpClient, "request")
    def test_get_cheques_rechazados_success(self, mock_request: MagicMock) -> None:
        """Test successful rejected checks retrieval."""
        mock_request.return_value = {
            "status": 200,
            "results": {
                "identificacion": 20123456789,
                "denominacion": "PERSONA TEST",
                "causales": [
                    {
                        "causal": "SIN FONDOS",
                        "entidades": [
                            {
                                "entidad": 1,
                                "detalle": [
                                    {
                                        "nroCheque": 752395,
                                        "fechaRechazo": "2024-04-08",
                                        "monto": 115000.00,
                                        "fechaPago": None,
                                        "fechaPagoMulta": None,
                                        "estadoMulta": "IMPAGA",
                                        "ctaPersonal": False,
                                        "denomJuridica": "EMPRESA S.R.L.",
                                        "enRevision": False,
                                        "procesoJud": False,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        }

        connector = BCRAConnector()
        result = connector.deudores.rejected_checks("20123456789")

        assert result.identificacion == 20123456789
        assert len(result.causales) == 1
        assert result.causales[0].causal == "SIN FONDOS"

    @patch.object(HttpClient, "request")
    def test_get_cheques_rechazados_empty(self, mock_request: MagicMock) -> None:
        """Test retrieval with no rejected checks."""
        mock_request.return_value = {
            "status": 200,
            "results": {
                "identificacion": 20123456789,
                "denominacion": "PERSONA SIN CHEQUES",
                "causales": [],
            },
        }

        connector = BCRAConnector()
        result = connector.deudores.rejected_checks("20123456789")

        assert result.identificacion == 20123456789
        assert len(result.causales) == 0

    def test_get_cheques_rechazados_invalid_identificacion(self) -> None:
        """Test validation of invalid identificacion."""
        connector = BCRAConnector()
        with pytest.raises(ValueError, match="exactly 11 digits"):
            connector.deudores.rejected_checks("invalid")

    @patch.object(HttpClient, "request")
    def test_get_cheques_rechazados_api_error(self, mock_request: MagicMock) -> None:
        """Test handling of API error."""
        mock_request.side_effect = BCRAApiError("Not found")

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError):
            connector.deudores.rejected_checks("20123456789")

    @patch.object(HttpClient, "request")
    def test_get_cheques_rechazados_invalid_response(
        self, mock_request: MagicMock
    ) -> None:
        """Test handling of invalid API response (missing results)."""
        mock_request.return_value = {"status": 200}

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Invalid response format"):
            connector.deudores.rejected_checks("20123456789")

    @patch.object(HttpClient, "request")
    def test_get_cheques_rechazados_results_not_dict(
        self, mock_request: MagicMock
    ) -> None:
        """Test handling when results is not a dict."""
        mock_request.return_value = {"status": 200, "results": []}

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Invalid response format"):
            connector.deudores.rejected_checks("20123456789")


class TestConnectorExceptionHandling:
    """Tests for exception handling branches in Central de Deudores methods."""

    @patch.object(HttpClient, "request")
    def test_get_deudas_key_error(self, mock_request: MagicMock) -> None:
        """Test KeyError handling when parsing response."""
        # Missing required 'identificacion' key
        mock_request.return_value = {
            "status": 200,
            "results": {"denominacion": "TEST", "periodos": []},
        }

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Unexpected response format"):
            connector.deudores.debts("20123456789")

    @patch.object(HttpClient, "request")
    def test_get_deudas_historicas_invalid_response(
        self, mock_request: MagicMock
    ) -> None:
        """Test handling when results is not a dict."""
        mock_request.return_value = {"status": 200, "results": "invalid"}

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Invalid response format"):
            connector.deudores.historical("20123456789")

    @patch.object(HttpClient, "request")
    def test_get_deudas_historicas_key_error(self, mock_request: MagicMock) -> None:
        """Test KeyError handling when parsing historical response."""
        mock_request.return_value = {
            "status": 200,
            "results": {"identificacion": 20123456789, "periodos": []},
        }

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Unexpected response format"):
            connector.deudores.historical("20123456789")

    @patch.object(HttpClient, "request")
    def test_get_cheques_rechazados_key_error(self, mock_request: MagicMock) -> None:
        """Test KeyError handling when parsing cheques response."""
        mock_request.return_value = {
            "status": 200,
            "results": {"identificacion": 20123456789, "causales": []},
        }

        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Unexpected response format"):
            connector.deudores.rejected_checks("20123456789")


class TestDeprecatedAliases:
    """The old connector methods delegate and warn until 1.0."""

    @pytest.mark.parametrize(
        "old,new,argument",
        [
            ("get_deudas", "debts", "20123456789"),
            ("get_deudas_historicas", "historical", "20123456789"),
            ("get_cheques_rechazados", "rejected_checks", "20123456789"),
        ],
    )
    def test_alias_warns_and_delegates(self, old: str, new: str, argument: str) -> None:
        connector = BCRAConnector()
        sentinel = object()
        with patch.object(
            connector.deudores, new, return_value=sentinel
        ) as mock_method:
            with pytest.warns(DeprecationWarning, match=f"deudores.{new}"):
                result = getattr(connector, old)(argument)
        mock_method.assert_called_once_with(argument)
        assert result is sentinel


class TestSharedParsing:
    """DomainClient._object turns any parsing failure into a BCRAApiError."""

    @patch.object(HttpClient, "request")
    def test_results_not_a_dict(self, mock_request: MagicMock) -> None:
        mock_request.return_value = {"status": 200, "results": []}
        connector = BCRAConnector()
        with pytest.raises(BCRAApiError, match="Invalid response format for deudas"):
            connector.deudores.debts("20123456789")

    @patch.object(HttpClient, "request")
    def test_parser_error_names_the_endpoint(self, mock_request: MagicMock) -> None:
        mock_request.return_value = {"status": 200, "results": {"unexpected": 1}}
        connector = BCRAConnector()
        with pytest.raises(
            BCRAApiError, match="Unexpected response format for deudas historicas"
        ):
            connector.deudores.historical("20123456789")

    @patch.object(HttpClient, "request")
    def test_unexpected_error_is_wrapped(self, mock_request: MagicMock) -> None:
        mock_request.return_value = {"status": 200, "results": {"x": 1}}
        connector = BCRAConnector()
        with patch(
            "bcra_connector.clients.deudores.ChequesRechazados.from_dict",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(
                BCRAApiError, match="Error fetching cheques rechazados: boom"
            ):
                connector.deudores.rejected_checks("20123456789")
