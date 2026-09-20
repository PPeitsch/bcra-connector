"""The superseded model exports warn when they are reached (issue #140)."""

import importlib
from typing import Any

import pytest

import bcra_connector

# name -> (module it is imported from, text the warning must carry)
PAGE = "use the Page"
ERROR = "raised as a BCRAApiError"

PACKAGE_EXPORTS = [
    ("bcra_connector.principales_variables", "DatosVariableResponse", PAGE),
    ("bcra_connector.cheques", "EntidadResponse", PAGE),
    ("bcra_connector.cheques", "ChequeResponse", PAGE),
    ("bcra_connector.cheques", "ErrorResponse", ERROR),
    ("bcra_connector.estadisticas_cambiarias", "DivisaResponse", PAGE),
    ("bcra_connector.estadisticas_cambiarias", "CotizacionResponse", PAGE),
    ("bcra_connector.estadisticas_cambiarias", "CotizacionesResponse", PAGE),
    ("bcra_connector.estadisticas_cambiarias", "ErrorResponse", ERROR),
]

TOP_LEVEL_EXPORTS = [
    ("DatosVariableResponse", PAGE),
    ("EntidadResponse", PAGE),
    ("ChequeResponse", PAGE),
    ("ChequesErrorResponse", ERROR),
    ("DivisaResponse", PAGE),
    ("CotizacionResponse", PAGE),
    ("CotizacionesResponse", PAGE),
    ("CambiariasErrorResponse", ERROR),
    ("EstadisticasCambiariasResultset", "use bcra_connector.Resultset"),
    ("EstadisticasCambiariasMetadata", "use bcra_connector.Metadata"),
]


class TestTheyWarn:
    """Reaching a superseded name says so, and names the replacement."""

    @pytest.mark.parametrize(
        "module,name,hint",
        PACKAGE_EXPORTS,
        ids=[f"{m.rsplit('.', 1)[-1]}.{n}" for m, n, _ in PACKAGE_EXPORTS],
    )
    def test_package_export_warns(self, module: str, name: str, hint: str) -> None:
        package = importlib.import_module(module)
        with pytest.warns(DeprecationWarning, match=f"{name} is deprecated"):
            attribute = getattr(package, name)
        assert attribute is not None
        with pytest.warns(DeprecationWarning, match=hint):
            getattr(package, name)

    @pytest.mark.parametrize(
        "name,hint", TOP_LEVEL_EXPORTS, ids=[n for n, _ in TOP_LEVEL_EXPORTS]
    )
    def test_top_level_export_warns(self, name: str, hint: str) -> None:
        with pytest.warns(DeprecationWarning, match=hint):
            assert getattr(bcra_connector, name) is not None


class TestTheyStillWork:
    """Deprecated is not broken: the classes behave as they did."""

    def test_the_class_is_the_one_it_always_was(self) -> None:
        from bcra_connector.cheques.cheques import ErrorResponse

        with pytest.warns(DeprecationWarning):
            assert bcra_connector.ChequesErrorResponse is ErrorResponse

    def test_it_still_parses(self) -> None:
        with pytest.warns(DeprecationWarning):
            error = bcra_connector.ChequesErrorResponse.from_dict(
                {"status": 404, "errorMessages": ["no encontrado"]}
            )
        assert error.status == 404
        assert error.error_messages == ["no encontrado"]

    def test_they_stay_in_all(self) -> None:
        for name, _ in TOP_LEVEL_EXPORTS:
            assert name in bcra_connector.__all__


class TestNothingElseChanged:
    """The shim covers the listed names only."""

    def test_importing_the_package_does_not_warn(
        self, recwarn: pytest.WarningsRecorder
    ) -> None:
        importlib.reload(bcra_connector)
        assert [w for w in recwarn if issubclass(w.category, DeprecationWarning)] == []

    def test_a_live_name_does_not_warn(self, recwarn: pytest.WarningsRecorder) -> None:
        assert bcra_connector.Page is not None
        assert bcra_connector.Resultset is not None
        assert len(recwarn) == 0

    @pytest.mark.parametrize(
        "module",
        [
            "bcra_connector",
            "bcra_connector.cheques",
            "bcra_connector.estadisticas_cambiarias",
            "bcra_connector.principales_variables",
        ],
    )
    def test_an_unknown_name_still_raises(self, module: str) -> None:
        package: Any = importlib.import_module(module)
        with pytest.raises(AttributeError, match="NoSuchModel"):
            package.NoSuchModel
