"""Tests for the per-instance cache of reference catalogs used in lookups."""

from datetime import date
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Cheque, Entidad
from bcra_connector.principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
from bcra_connector.principales_variables.principales_variables import (
    Metadata,
    Resultset,
)

CATALOG = [
    PrincipalesVariables(idVariable=1, descripcion="Reservas internacionales"),
    PrincipalesVariables(idVariable=15, descripcion="Base monetaria"),
]


def _series(id_variable: int, *args: object, **kwargs: object) -> DatosVariableResponse:
    detalle = [
        DetalleMonetaria(fecha=date(2024, 1, d), valor=float(d * id_variable))
        for d in (3, 2, 1)
    ]
    return DatosVariableResponse(
        status=200,
        metadata=Metadata(resultset=Resultset(count=3, offset=0, limit=3000)),
        results=[DatosVariable(idVariable=id_variable, detalle=detalle)],
    )


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


@pytest.fixture
def catalog(connector: BCRAConnector) -> Iterator[MagicMock]:
    with (
        patch.object(
            connector, "get_principales_variables", return_value=CATALOG
        ) as mock_catalog,
        patch.object(connector, "get_datos_variable", side_effect=_series),
    ):
        yield mock_catalog


class TestVariableCatalogCache:
    def test_report_fetches_catalog_once(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        connector.generate_variable_report("Reservas internacionales")
        assert catalog.call_count == 1

    def test_correlation_fetches_catalog_once(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        connector.get_variable_correlation("Reservas internacionales", "Base monetaria")
        assert catalog.call_count == 1

    def test_repeated_lookups_reuse_catalog(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        for _ in range(3):
            connector.get_variable_history("Base monetaria", days=10)
        assert catalog.call_count == 1

    def test_expires_after_ttl(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        clock = "bcra_connector._http.time.monotonic"
        ttl = connector.CATALOG_CACHE_TTL
        with patch(clock, return_value=1000.0):
            connector.get_variable_by_name("Base monetaria")
        with patch(clock, return_value=1000.0 + ttl - 1):
            connector.get_variable_by_name("Base monetaria")
        assert catalog.call_count == 1
        with patch(clock, return_value=1000.0 + ttl):
            connector.get_variable_by_name("Base monetaria")
        assert catalog.call_count == 2

    def test_clear_cache_forces_refetch(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        connector.get_variable_by_name("Base monetaria")
        connector.clear_cache()
        connector.get_variable_by_name("Base monetaria")
        assert catalog.call_count == 2

    def test_ttl_zero_disables_cache(
        self,
        connector: BCRAConnector,
        catalog: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(connector, "CATALOG_CACHE_TTL", 0)
        connector.get_variable_by_name("Base monetaria")
        connector.get_variable_by_name("Base monetaria")
        assert catalog.call_count == 2

    def test_errors_are_not_cached(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector,
            "get_principales_variables",
            side_effect=[BCRAApiError("down"), CATALOG],
        ) as mock_catalog:
            with pytest.raises(BCRAApiError):
                connector.get_variable_by_name("Base monetaria")
            variable = connector.get_variable_by_name("Base monetaria")
        assert variable is not None and variable.idVariable == 15
        assert mock_catalog.call_count == 2

    def test_public_catalog_call_is_not_cached(self, connector: BCRAConnector) -> None:
        """get_principales_variables() is the explicit "fresh data" call."""
        response = {"results": [{"idVariable": 1, "descripcion": "Reservas"}]}
        with patch.object(
            connector, "_make_request", return_value=response
        ) as mock_req:
            connector.get_principales_variables()
            connector.get_principales_variables()
        assert mock_req.call_count == 2


class TestEntitiesCache:
    def test_check_denunciado_reuses_entities(self, connector: BCRAConnector) -> None:
        entities = [Entidad(codigo_entidad=11, denominacion="BANCO DE LA NACION")]
        cheque = Cheque(
            numero_cheque=1,
            denunciado=True,
            fecha_procesamiento=date(2024, 1, 1),
            denominacion_entidad="BANCO DE LA NACION",
            detalles=[],
        )
        with (
            patch.object(
                connector, "get_entidades", return_value=entities
            ) as mock_entities,
            patch.object(connector, "get_cheque_denunciado", return_value=cheque),
        ):
            assert connector.check_denunciado("banco de la nacion", 1)
            assert connector.check_denunciado("BANCO DE LA NACION", 2)
        assert mock_entities.call_count == 1
