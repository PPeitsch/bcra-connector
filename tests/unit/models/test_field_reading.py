"""One way to read a field out of an API response (issue #145).

Every ``from_dict`` goes through :func:`require` / :func:`optional`, so a malformed
payload fails the same way — naming the field and what was expected — whichever
endpoint produced it.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Type
from unittest.mock import patch

import pytest

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.central_deudores import ChequeRechazado, Deudor, EntidadDeuda
from bcra_connector.cheques import Cheque, Entidad
from bcra_connector.estadisticas_cambiarias import CotizacionDetalle, Divisa
from bcra_connector.models import optional, require
from bcra_connector.principales_variables import (
    DetalleMonetaria,
    PrincipalesVariables,
)


class TestRequire:
    """The reader every model uses for a field the API always sends."""

    def test_missing_field_names_itself(self) -> None:
        with pytest.raises(ValueError, match="field 'codigo' is missing"):
            require({}, "codigo", str)

    def test_none_is_not_a_value(self) -> None:
        """A null is a malformed payload for a required field, not a default."""
        with pytest.raises(ValueError, match="field 'count' must be int"):
            require({"count": None}, "count", int)

    @pytest.mark.parametrize(
        ("value", "kind", "expected"),
        [
            ("100", int, 100),
            (100, int, 100),
            ("1.5", float, 1.5),
            (2, float, 2.0),
            (7, str, "7"),
            ("USD", str, "USD"),
            (True, bool, True),
            (0, bool, False),
            ("2024-01-31", date, date(2024, 1, 31)),
            (datetime(2024, 1, 31, 12), date, date(2024, 1, 31)),
            (date(2024, 1, 31), date, date(2024, 1, 31)),
        ],
    )
    def test_conversions(self, value: Any, kind: type, expected: Any) -> None:
        assert require({"f": value}, "f", kind) == expected

    @pytest.mark.parametrize(
        ("value", "kind", "message"),
        [
            ("not-a-number", int, "field 'f' must be int, got 'not-a-number'"),
            ("not-a-number", float, "field 'f' must be float"),
            ({"a": 1}, str, "field 'f' must be a string, got dict"),
            ([1], str, "field 'f' must be a string, got list"),
            ("not-a-date", date, "'f' must be an ISO 8601 date"),
            (17, date, "'f' must be a date, a datetime or an ISO 8601 string"),
            ("not a list", list, "field 'f' must be a list, got str"),
            ("not an object", dict, "field 'f' must be an object, got str"),
            ([], dict, "field 'f' must be an object, got list"),
        ],
    )
    def test_unreadable_values(self, value: Any, kind: type, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            require({"f": value}, "f", kind)

    def test_wrong_date_type_is_a_value_error(self) -> None:
        """``as_date`` says TypeError; the helpers only ever raise ValueError."""
        with pytest.raises(ValueError):
            require({"f": 17}, "f", date)

    def test_containers_are_not_copied(self) -> None:
        rows: List[int] = [1, 2]
        assert require({"f": rows}, "f", list) is rows


class TestOptional:
    """The reader for a field the API may omit or report as null."""

    def test_missing_yields_the_default(self) -> None:
        assert optional({}, "f", str) is None
        assert optional({}, "f", bool, default=False) is False
        assert optional({}, "f", list, default=[]) == []

    def test_null_yields_the_default(self) -> None:
        assert optional({"f": None}, "f", date) is None

    def test_a_present_value_is_converted(self) -> None:
        assert optional({"f": "2024-01-31"}, "f", date) == date(2024, 1, 31)

    def test_a_present_bad_value_still_fails(self) -> None:
        with pytest.raises(ValueError, match="field 'f' must be float"):
            optional({"f": "nope"}, "f", float)


MISSING_FIELD: List[Any] = [
    (Entidad, {"codigoEntidad": 7}, "field 'denominacion' is missing"),
    (Divisa, {"codigo": "USD"}, "field 'denominacion' is missing"),
    (
        CotizacionDetalle,
        {"codigoMoneda": "USD", "descripcion": "DOLAR", "tipoPase": 1.0},
        "field 'tipoCotizacion' is missing",
    ),
    (DetalleMonetaria, {"valor": 1.0}, "field 'fecha' is missing"),
    (PrincipalesVariables, {"descripcion": "x"}, "field 'idVariable' is missing"),
    (
        EntidadDeuda,
        {"entidad": "BANCO", "situacion": 1},
        "field 'monto' is missing",
    ),
    (Deudor, {"identificacion": 20000000001}, "field 'denominacion' is missing"),
    (
        ChequeRechazado,
        {"nroCheque": 1, "monto": 10.0},
        "field 'fechaRechazo' is missing",
    ),
    (
        Cheque,
        {"numeroCheque": 1, "denunciado": False, "fechaProcesamiento": "2024-01-01"},
        "field 'denominacionEntidad' is missing",
    ),
]


@pytest.mark.parametrize(("model", "payload", "message"), MISSING_FIELD)
def test_every_model_reports_the_field_it_could_not_read(
    model: Type[Any], payload: Dict[str, Any], message: str
) -> None:
    """The same failure across the four domains, not a bare KeyError."""
    with pytest.raises(ValueError, match=message):
        model.from_dict(payload)


def test_the_message_composes_with_the_endpoint() -> None:
    """The helper names the field; the domain client names what was being read."""
    connector = BCRAConnector(rate_limit=None)
    with patch.object(
        connector._http, "request", return_value={"results": [{"denominacion": "X"}]}
    ):
        with pytest.raises(BCRAApiError) as exc:
            connector.cheques.entities()
    assert "financial entities" in str(exc.value)
    assert "field 'codigoEntidad' is missing" in str(exc.value)
