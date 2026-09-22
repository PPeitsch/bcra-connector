"""Tests for the cambiarias sub-client."""

from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


class TestTransportShims:
    """`_collect_pages` stays on the connector for code that patched it."""

    def test_collect_pages_delegates(self, connector: BCRAConnector) -> None:
        pages = [([1, 2], None), ([3], None)]
        result = connector._collect_pages(
            lambda limit, offset: pages[offset // 2], 2, "things"
        )
        assert result == [1, 2, 3]


class TestPageSize:
    """``fx_page_size`` reaches the client, which asks the API for that limit."""

    def test_the_argument_reaches_the_client(self) -> None:
        connector = BCRAConnector(fx_page_size=10)
        assert connector._http.config.fx_max_page_size == 10
        with patch.object(
            connector._http, "request", return_value={"results": []}
        ) as mock_req:
            connector.cambiarias.evolution("USD", days=5)
        assert mock_req.call_args.kwargs["params"]["limit"] == 10
