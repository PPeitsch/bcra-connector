"""Every date input accepts a date, a datetime or an ISO string (issue #133)."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector

# The same day, in each of the three accepted forms.
DAY = date(2024, 1, 2)
FORMS = [DAY, datetime(2024, 1, 2, 15, 30), "2024-01-02"]
IDS = ["date", "datetime", "str"]

EMPTY_LIST: Dict[str, Any] = {"results": []}
EMPTY_QUOTATION: Dict[str, Any] = {"results": {"fecha": None, "detalle": []}}


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


def _params(mock: Any) -> Optional[Dict[str, Any]]:
    """The params of the single request the client made."""
    _, kwargs = mock.call_args
    if "params" in kwargs:
        params: Optional[Dict[str, Any]] = kwargs["params"]
        return params
    positional: Optional[Dict[str, Any]] = mock.call_args[0][1]
    return positional


class TestMonetariasSeries:
    """``desde``/``hasta`` reach the API as YYYY-MM-DD whatever they came as."""

    @pytest.mark.parametrize("value", FORMS, ids=IDS)
    def test_every_form_sends_the_same_range(
        self, connector: BCRAConnector, value: Any
    ) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_LIST
        ) as request:
            connector.monetarias.series(1, desde=value, hasta=value)
        assert _params(request) == {"Desde": "2024-01-02", "Hasta": "2024-01-02"}

    def test_range_is_compared_across_types(self, connector: BCRAConnector) -> None:
        with pytest.raises(ValueError, match="'desde' date must be earlier"):
            connector.monetarias.series(1, desde="2024-02-01", hasta=DAY)

    @pytest.mark.parametrize("param", ["desde", "hasta"])
    def test_bad_string_names_the_parameter(
        self, connector: BCRAConnector, param: str
    ) -> None:
        with pytest.raises(ValueError, match=f"'{param}' must be an ISO 8601 date"):
            connector.monetarias.series(1, **{param: "02/01/2024"})

    def test_no_dates_sends_no_date_params(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_LIST
        ) as request:
            connector.monetarias.series(1)
        assert _params(request) is None


class TestCambiariasQuotations:
    """``fecha`` is normalized before it reaches the query string."""

    @pytest.mark.parametrize("value", FORMS, ids=IDS)
    def test_every_form_sends_the_same_date(
        self, connector: BCRAConnector, value: Any
    ) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_QUOTATION
        ) as request:
            connector.cambiarias.quotations(value)
        assert _params(request) == {"fecha": "2024-01-02"}

    def test_bad_string_raises_before_the_request(
        self, connector: BCRAConnector
    ) -> None:
        with patch.object(connector._http, "request") as request:
            with pytest.raises(ValueError, match="'fecha' must be an ISO 8601 date"):
                connector.cambiarias.quotations("02/01/2024")
        request.assert_not_called()

    def test_none_asks_for_the_latest(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_QUOTATION
        ) as request:
            connector.cambiarias.quotations()
        assert _params(request) is None


class TestCambiariasSeries:
    """``fecha_desde``/``fecha_hasta``, same deal."""

    @pytest.mark.parametrize("value", FORMS, ids=IDS)
    def test_every_form_sends_the_same_range(
        self, connector: BCRAConnector, value: Any
    ) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_LIST
        ) as request:
            connector.cambiarias.series("USD", fecha_desde=value, fecha_hasta=value)
        assert _params(request) == {
            "fechaDesde": "2024-01-02",
            "fechaHasta": "2024-01-02",
            "limit": 1000,
            "offset": 0,
        }

    @pytest.mark.parametrize("param", ["fecha_desde", "fecha_hasta"])
    def test_bad_string_names_the_parameter(
        self, connector: BCRAConnector, param: str
    ) -> None:
        with pytest.raises(ValueError, match=f"'{param}' must be an ISO 8601 date"):
            connector.cambiarias.series("USD", **{param: "02/01/2024"})

    def test_unsupported_type_raises_type_error(self, connector: BCRAConnector) -> None:
        with pytest.raises(TypeError, match="'fecha_desde' must be a date"):
            connector.cambiarias.series("USD", fecha_desde=20240102)


class TestDeprecatedAliasesAcceptThemToo:
    """The 0.12 methods widen along with the sub-clients."""

    def test_get_datos_variable_takes_a_date(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_LIST
        ) as request:
            with pytest.warns(DeprecationWarning):
                connector.get_datos_variable(1, desde=DAY, hasta=DAY)
        assert _params(request) == {"Desde": "2024-01-02", "Hasta": "2024-01-02"}

    def test_get_cotizaciones_takes_a_date(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_QUOTATION
        ) as request:
            with pytest.warns(DeprecationWarning):
                connector.get_cotizaciones(DAY)
        assert _params(request) == {"fecha": "2024-01-02"}

    def test_get_evolucion_moneda_takes_dates(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_LIST
        ) as request:
            with pytest.warns(DeprecationWarning):
                connector.get_evolucion_moneda("USD", DAY, DAY)
        params = _params(request) or {}
        assert params["fechaDesde"] == "2024-01-02"
        assert params["fechaHasta"] == "2024-01-02"


class TestEvolutionRange:
    """``evolution`` builds its own range; it must send dates, not datetimes."""

    def test_sends_plain_dates(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector._http, "request", return_value=EMPTY_LIST
        ) as request:
            connector.cambiarias.evolution("USD", days=7, limit=100)
        params = _params(request) or {}
        assert date.fromisoformat(params["fechaDesde"]) == date.today() - timedelta(
            days=7
        )
        assert date.fromisoformat(params["fechaHasta"]) == date.today()
