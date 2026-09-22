"""Tests for the per-instance cache of reference catalogs used in lookups."""

from datetime import date
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Cheque, Entidad
from bcra_connector.models import Page
from bcra_connector.principales_variables import (
    DatosVariable,
    DetalleMonetaria,
    PrincipalesVariables,
)

CATALOG = [
    PrincipalesVariables(id_variable=1, descripcion="Reservas internacionales"),
    PrincipalesVariables(id_variable=15, descripcion="Base monetaria"),
]


def _series(id_variable: int, *args: object, **kwargs: object) -> Page[DatosVariable]:
    detalle = [
        DetalleMonetaria(fecha=date(2024, 1, d), valor=float(d * id_variable))
        for d in (3, 2, 1)
    ]
    return Page(
        [DatosVariable(id_variable=id_variable, detalle=detalle)],
        count=3,
        offset=0,
        limit=3000,
    )


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


@pytest.fixture
def catalog(connector: BCRAConnector) -> Iterator[MagicMock]:
    with (
        patch.object(
            connector.monetarias, "list", return_value=Page(CATALOG)
        ) as mock_catalog,
        patch.object(connector.monetarias, "series", side_effect=_series),
    ):
        yield mock_catalog


class TestVariableCatalogCache:
    def test_a_lookup_fetches_the_catalog_once(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        connector.monetarias.history("Reservas internacionales", days=10)
        assert catalog.call_count == 1

    def test_two_different_names_share_one_fetch(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        """The cache is keyed by catalog, not by name: a second name reuses it."""
        connector.monetarias.find("Reservas internacionales")
        connector.monetarias.find("Base monetaria")
        assert catalog.call_count == 1

    def test_repeated_lookups_reuse_catalog(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        for _ in range(3):
            connector.monetarias.history("Base monetaria", days=10)
        assert catalog.call_count == 1

    def test_expires_after_ttl(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        clock = "bcra_connector._http.time.monotonic"
        ttl = connector.CATALOG_CACHE_TTL
        with patch(clock, return_value=1000.0):
            connector.monetarias.find("Base monetaria")
        with patch(clock, return_value=1000.0 + ttl - 1):
            connector.monetarias.find("Base monetaria")
        assert catalog.call_count == 1
        with patch(clock, return_value=1000.0 + ttl):
            connector.monetarias.find("Base monetaria")
        assert catalog.call_count == 2

    def test_clear_cache_forces_refetch(
        self, connector: BCRAConnector, catalog: MagicMock
    ) -> None:
        connector.monetarias.find("Base monetaria")
        connector.clear_cache()
        connector.monetarias.find("Base monetaria")
        assert catalog.call_count == 2

    def test_ttl_zero_disables_cache(
        self,
        connector: BCRAConnector,
        catalog: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(connector, "CATALOG_CACHE_TTL", 0)
        connector.monetarias.find("Base monetaria")
        connector.monetarias.find("Base monetaria")
        assert catalog.call_count == 2

    def test_errors_are_not_cached(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector.monetarias,
            "list",
            side_effect=[BCRAApiError("down"), Page(CATALOG)],
        ) as mock_catalog:
            with pytest.raises(BCRAApiError):
                connector.monetarias.find("Base monetaria")
            variable = connector.monetarias.find("Base monetaria")
        assert variable is not None and variable.id_variable == 15
        assert mock_catalog.call_count == 2

    def test_public_catalog_call_is_not_cached(self, connector: BCRAConnector) -> None:
        """monetarias.list() is the explicit "fresh data" call."""
        response = {"results": [{"idVariable": 1, "descripcion": "Reservas"}]}
        with patch.object(
            connector._http, "request", return_value=response
        ) as mock_req:
            connector.monetarias.list()
            connector.monetarias.list()
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
                connector.cheques, "entities", return_value=entities
            ) as mock_entities,
            patch.object(connector.cheques, "reported", return_value=cheque),
        ):
            assert connector.cheques.is_reported("banco de la nacion", 1)
            assert connector.cheques.is_reported("BANCO DE LA NACION", 2)
        assert mock_entities.call_count == 1
