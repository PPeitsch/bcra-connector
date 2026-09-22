"""Tests for automatic pagination: no helper may silently truncate results."""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector
from bcra_connector.principales_variables import PrincipalesVariables
from bcra_connector.rate_limiter import RateLimitConfig

PAGE = 10  # smallest page size the APIs accept


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector(
        page_size=PAGE,
        fx_page_size=PAGE,
        rate_limit=RateLimitConfig(calls=1000, period=1.0),
    )


def _catalog_page(params: Dict[str, Any], total: int) -> Dict[str, Any]:
    offset, limit = params["Offset"], params["Limit"]
    ids = range(offset, min(offset + limit, total))
    # The catalog reports the count from the offset on, not the total.
    return {
        "status": 200,
        "metadata": {
            "resultset": {"count": total - offset, "offset": offset, "limit": limit}
        },
        "results": [{"idVariable": i, "descripcion": f"Var {i}"} for i in ids],
    }


def _series_page(params: Dict[str, Any], total: int) -> Dict[str, Any]:
    offset, limit = params.get("Offset", 0), params["Limit"]
    start = date(2020, 1, 1)
    detalle = [
        {"fecha": (start + timedelta(days=i)).isoformat(), "valor": float(i)}
        for i in range(offset, min(offset + limit, total))
    ]
    return {
        "status": 200,
        "metadata": {"resultset": {"count": total, "offset": offset, "limit": limit}},
        "results": [{"idVariable": 1, "detalle": detalle}] if detalle else [],
    }


def _fx_page(params: Dict[str, Any], total: int) -> Dict[str, Any]:
    offset, limit = params["offset"], params["limit"]
    start = date(2020, 1, 1)
    results = [
        {
            "fecha": (start + timedelta(days=i)).isoformat(),
            "detalle": [
                {
                    "codigoMoneda": "USD",
                    "descripcion": "DOLAR",
                    "tipoPase": 1.0,
                    "tipoCotizacion": 1000.0 + i,
                }
            ],
        }
        for i in range(offset, min(offset + limit, total))
    ]
    return {
        "status": 200,
        "metadata": {"resultset": {"count": total, "offset": offset, "limit": limit}},
        "results": results,
    }


class TestCatalog:
    def test_returns_every_page(self, connector: BCRAConnector) -> None:
        total = 2 * PAGE + 3
        with patch.object(
            connector._http,
            "request",
            side_effect=lambda endpoint, params: _catalog_page(params, total),
        ) as mock_req:
            variables = connector.monetarias.list()

        assert [v.id_variable for v in variables] == list(range(total))
        assert mock_req.call_count == 3

    def test_exact_multiple_of_page_size(self, connector: BCRAConnector) -> None:
        total = 2 * PAGE
        with patch.object(
            connector._http,
            "request",
            side_effect=lambda endpoint, params: _catalog_page(params, total),
        ) as mock_req:
            variables = connector.monetarias.list()

        assert len(variables) == total
        assert mock_req.call_count == 3  # the last, empty page ends the listing


class TestVariableHistory:
    def _history(
        self, connector: BCRAConnector, total: int, **kwargs: Any
    ) -> List[Any]:
        variable = PrincipalesVariables(id_variable=1, descripcion="Var")
        with patch.object(connector.monetarias, "find", return_value=variable):
            with patch.object(
                connector._http,
                "request",
                side_effect=lambda endpoint, params: _series_page(params, total),
            ) as mock_req:
                points: List[Any] = connector.monetarias.history(
                    "Var", days=3650, **kwargs
                )
        self.calls = mock_req.call_count
        return points

    def test_without_limit_returns_every_page(self, connector: BCRAConnector) -> None:
        points = self._history(connector, total=2 * PAGE + 5)
        assert len(points) == 2 * PAGE + 5
        assert self.calls == 3

    def test_stops_at_reported_total(self, connector: BCRAConnector) -> None:
        points = self._history(connector, total=2 * PAGE)
        assert len(points) == 2 * PAGE
        assert self.calls == 2  # series report the real total: no empty page needed

    def test_explicit_limit_is_a_single_page(self, connector: BCRAConnector) -> None:
        points = self._history(connector, total=5 * PAGE, limit=PAGE)
        assert len(points) == PAGE
        assert self.calls == 1


class TestCurrencyEvolution:
    def _evolution(self, connector: BCRAConnector, total: int, **kwargs: Any):
        with patch.object(
            connector._http,
            "request",
            side_effect=lambda endpoint, params: _fx_page(params, total),
        ) as mock_req:
            result = connector.cambiarias.evolution("USD", days=3650, **kwargs)
        self.calls = mock_req.call_count
        return result

    def test_default_returns_whole_range(self, connector: BCRAConnector) -> None:
        result = self._evolution(connector, total=3 * PAGE + 1)
        assert len(result) == 3 * PAGE + 1
        assert self.calls == 4

    def test_offset_without_limit_pages_from_offset(
        self, connector: BCRAConnector
    ) -> None:
        result = self._evolution(connector, total=3 * PAGE, offset=PAGE)
        assert len(result) == 2 * PAGE
        assert result[0].fecha == date(2020, 1, 1) + timedelta(days=PAGE)

    def test_pair_evolution_no_longer_limited_by_days(
        self, connector: BCRAConnector
    ) -> None:
        """days + 15 used to exceed the API's 1000 limit and raise ValueError."""
        with patch.object(
            connector._http,
            "request",
            side_effect=lambda endpoint, params: _fx_page(params, 2 * PAGE),
        ):
            pairs = connector.cambiarias.pair("USD", "USD", days=2000)
        assert len(pairs) == 2 * PAGE

    def test_single_page_call_warns_when_truncated(
        self, connector: BCRAConnector, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch.object(
            connector._http,
            "request",
            side_effect=lambda endpoint, params: _fx_page(params, 3 * PAGE),
        ):
            with caplog.at_level(logging.WARNING, logger="bcra_connector"):
                result = connector.cambiarias.series("USD", limit=PAGE)

        assert len(result) == PAGE
        assert any(
            f"Returned {PAGE} of {3 * PAGE} quotations" in r.getMessage()
            for r in caplog.records
        )

    def test_single_page_call_complete_does_not_warn(
        self, connector: BCRAConnector, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch.object(
            connector._http,
            "request",
            side_effect=lambda endpoint, params: _fx_page(params, PAGE),
        ):
            with caplog.at_level(logging.WARNING, logger="bcra_connector"):
                connector.cambiarias.series("USD", limit=PAGE)
        assert not [r for r in caplog.records if r.levelname == "WARNING"]


class TestSafetyCap:
    def test_stops_after_max_pages(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An endpoint that ignores Offset must not page forever."""
        connector = BCRAConnector(
            page_size=PAGE,
            fx_page_size=PAGE,
            max_pages=3,
            rate_limit=RateLimitConfig(calls=1000, period=1.0),
        )
        full_page = _catalog_page({"Offset": 0, "Limit": PAGE}, 10 * PAGE)
        with patch.object(
            connector._http, "request", return_value=full_page
        ) as mock_req:
            with caplog.at_level(logging.WARNING, logger="bcra_connector"):
                connector.monetarias.list()

        assert mock_req.call_count == 3
        assert any("Stopped paging" in r.getMessage() for r in caplog.records)
