"""Typed API exceptions and the cheques.is_reported() behavior built on them."""

import json
from datetime import date
from typing import Any, List
from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import HTTPError

from bcra_connector import (
    BCRAApiError,
    BCRAConnector,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from bcra_connector.cheques import Cheque, Entidad

ENTITIES = [
    Entidad(codigo_entidad=7, denominacion="BANCO DE GALICIA Y BUENOS AIRES S.A."),
    Entidad(codigo_entidad=11, denominacion="BANCO DE LA NACION ARGENTINA"),
    Entidad(codigo_entidad=72, denominacion="BANCO SANTANDER ARGENTINA S.A."),
    Entidad(codigo_entidad=300, denominacion="BANCO DE INVERSION Y COMERCIO EXTERIOR"),
    Entidad(codigo_entidad=301, denominacion="BANCO DE INVERSION"),
]


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector(rate_limit=None)


def _http_error_response(status: int, body: Any = None) -> Mock:
    response = Mock()
    response.status_code = status
    response.url = "https://api.bcra.gob.ar/test"
    response.reason = "Reason"
    if body is None:
        response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    else:
        response.json.return_value = body
    response.raise_for_status.side_effect = HTTPError(response=response)
    return response


def _request_error(connector: BCRAConnector, status: int) -> BCRAApiError:
    response = _http_error_response(status, {"errorMessages": ["detalle"]})
    with (
        patch.object(connector.session, "get", return_value=response),
        patch("bcra_connector._http.time.sleep"),
        pytest.raises(BCRAApiError) as exc_info,
    ):
        connector._make_request("test")
    return exc_info.value


def _cheque(denunciado: bool) -> Cheque:
    return Cheque(
        numero_cheque=1,
        denunciado=denunciado,
        fecha_procesamiento=date(2026, 9, 18),
        denominacion_entidad="BANCO DE LA NACION ARGENTINA",
        detalles=[],
    )


class TestHierarchy:
    @pytest.mark.parametrize(
        "cls", [BCRANotFoundError, BCRARateLimitError, BCRAServerError]
    )
    def test_subclasses_of_api_error(self, cls: type) -> None:
        assert issubclass(cls, BCRAApiError)

    def test_status_code_defaults_to_none(self) -> None:
        error = BCRAApiError("boom")
        assert error.status_code is None
        assert str(error) == "boom"

    def test_importable_from_old_module(self) -> None:
        from bcra_connector.bcra_connector import BCRAApiError as OldPath

        assert OldPath is BCRAApiError


class TestMakeRequestErrors:
    def test_404_is_not_found(self, connector: BCRAConnector) -> None:
        error = _request_error(connector, 404)
        assert type(error) is BCRANotFoundError
        assert error.status_code == 404
        assert "detalle" in str(error)

    def test_429_after_retries_is_rate_limit(self, connector: BCRAConnector) -> None:
        error = _request_error(connector, 429)
        assert type(error) is BCRARateLimitError
        assert error.status_code == 429

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_5xx_after_retries_is_server_error(
        self, connector: BCRAConnector, status: int
    ) -> None:
        error = _request_error(connector, status)
        assert type(error) is BCRAServerError
        assert error.status_code == status

    def test_other_4xx_is_base_error_with_status(
        self, connector: BCRAConnector
    ) -> None:
        error = _request_error(connector, 400)
        assert type(error) is BCRAApiError
        assert error.status_code == 400

    def test_timeout_has_no_status(self, connector: BCRAConnector) -> None:
        with (
            patch.object(connector.session, "get", side_effect=requests.Timeout()),
            patch("bcra_connector._http.time.sleep"),
            pytest.raises(BCRAApiError) as exc_info,
        ):
            connector._make_request("test")
        assert type(exc_info.value) is BCRAApiError
        assert exc_info.value.status_code is None

    def test_type_survives_endpoint_wrappers(self, connector: BCRAConnector) -> None:
        response = _http_error_response(404, {"errorMessages": ["No se encontró"]})
        with (
            patch.object(connector.session, "get", return_value=response),
            pytest.raises(BCRANotFoundError),
        ):
            connector.deudores.debts("20000000007")


class TestCheckDenunciado:
    def _check(
        self, connector: BCRAConnector, name: str, cheque: Any = None
    ) -> List[int]:
        """Run cheques.is_reported and return the entity codes it queried."""
        cheque = cheque if cheque is not None else _cheque(False)
        with (
            patch.object(connector.cheques, "entities", return_value=ENTITIES),
            patch.object(
                connector.cheques, "reported", return_value=cheque
            ) as mock_cheque,
        ):
            connector.cheques.is_reported(name, 1)
        return [c.args[0] for c in mock_cheque.call_args_list]

    def test_404_propagates_instead_of_false(self, connector: BCRAConnector) -> None:
        # The live API answers 200 + denunciado=false for a check that isn't
        # reported; its only 404 is "Entidad informada inexistente".
        with (
            patch.object(connector.cheques, "entities", return_value=ENTITIES),
            patch.object(
                connector.cheques,
                "reported",
                side_effect=BCRANotFoundError(
                    "Entidad informada inexistente.", status_code=404
                ),
            ),
            pytest.raises(BCRANotFoundError),
        ):
            connector.cheques.is_reported("BANCO DE LA NACION ARGENTINA", 1)

    def test_not_found_text_is_not_a_signal(self, connector: BCRAConnector) -> None:
        with (
            patch.object(connector.cheques, "entities", return_value=ENTITIES),
            patch.object(
                connector.cheques,
                "reported",
                side_effect=BCRAServerError("upstream not found", status_code=502),
            ),
            pytest.raises(BCRAServerError),
        ):
            connector.cheques.is_reported("BANCO DE LA NACION ARGENTINA", 1)

    def test_returns_api_flag(self, connector: BCRAConnector) -> None:
        with (
            patch.object(connector.cheques, "entities", return_value=ENTITIES),
            patch.object(connector.cheques, "reported", return_value=_cheque(True)),
        ):
            assert connector.cheques.is_reported("banco de la nacion argentina", 1)

    def test_accent_insensitive_exact(self, connector: BCRAConnector) -> None:
        assert self._check(connector, "Banco de la Nación Argentina") == [11]

    def test_unique_substring(self, connector: BCRAConnector) -> None:
        assert self._check(connector, "santander") == [72]
        assert self._check(connector, "  Galicia ") == [7]

    def test_exact_wins_over_substring(self, connector: BCRAConnector) -> None:
        # "banco de inversion" is also a substring of entity 300.
        assert self._check(connector, "Banco de Inversión") == [301]

    def test_ambiguous_substring_lists_candidates(
        self, connector: BCRAConnector
    ) -> None:
        with pytest.raises(ValueError, match="matches 2 entities") as exc_info:
            self._check(connector, "inversion")
        assert "BANCO DE INVERSION" in str(exc_info.value)

    def test_many_candidates_are_truncated(self, connector: BCRAConnector) -> None:
        entities = [
            Entidad(codigo_entidad=i, denominacion=f"BANCO {i:02d}") for i in range(15)
        ]
        with (
            patch.object(connector.cheques, "entities", return_value=entities),
            pytest.raises(ValueError, match="matches 15 entities") as exc_info,
        ):
            connector.cheques.is_reported("banco", 1)
        message = str(exc_info.value)
        assert "BANCO 09" in message and "BANCO 10" not in message
        assert "..." in message

    def test_unknown_entity(self, connector: BCRAConnector) -> None:
        with pytest.raises(ValueError, match="not found"):
            self._check(connector, "Banco Inexistente")


class TestFindEntity:
    """find_entity() resolves a name without making a request."""

    def test_usable_standalone(self, connector: BCRAConnector) -> None:
        entity = connector.cheques.find_entity(ENTITIES, "Banco de la Nación Argentina")
        assert entity.codigo_entidad == 11
