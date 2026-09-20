"""Tests for the cambiarias sub-client and its deprecated aliases."""

from typing import Any
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector
from bcra_connector.models import Page


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


class TestDeprecatedAliases:
    """The old connector methods delegate and warn until 1.0."""

    @pytest.mark.parametrize(
        "old,new,args,paged",
        [
            ("get_divisas", "currencies", (), True),
            ("get_cotizaciones", "quotations", ("2024-01-02",), False),
            (
                "get_evolucion_moneda",
                "series",
                ("USD", "2024-01-01", "2024-01-31", 50, 0),
                True,
            ),
            ("get_currency_evolution", "evolution", ("USD", 10, 100, 0), True),
            ("get_latest_quotations", "latest", (), False),
            ("get_currency_pair_evolution", "pair", ("USD", "ARS", 7), False),
        ],
    )
    def test_alias_warns_and_delegates(
        self, connector: BCRAConnector, old: str, new: str, args: Any, paged: bool
    ) -> None:
        rows = [object()]
        returned: Any = Page(rows, count=1) if paged else rows[0]
        with patch.object(
            connector.cambiarias, new, return_value=returned
        ) as mock_method:
            with pytest.warns(DeprecationWarning, match=f"cambiarias.{new}"):
                result = getattr(connector, old)(*args)
        mock_method.assert_called_once_with(*args)
        assert result == (rows if paged else rows[0])


class TestTransportShims:
    """`_collect_pages` stays on the connector for code that patched it."""

    def test_collect_pages_delegates(self, connector: BCRAConnector) -> None:
        pages = [([1, 2], None), ([3], None)]
        result = connector._collect_pages(
            lambda limit, offset: pages[offset // 2], 2, "things"
        )
        assert result == [1, 2, 3]


class TestPageSize:
    """The FX page size still comes from the class attribute (until 1.0)."""

    def test_subclass_override_reaches_the_client(self) -> None:
        class Small(BCRAConnector):
            FX_MAX_PAGE_SIZE = 10

        connector = Small()
        assert connector._http.config().fx_max_page_size == 10
        with patch.object(
            connector._http, "request", return_value={"results": []}
        ) as mock_req:
            connector.cambiarias.evolution("USD", days=5)
        assert mock_req.call_args.kwargs["params"]["limit"] == 10
