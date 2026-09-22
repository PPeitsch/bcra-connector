"""Tests for the monetarias sub-client."""

from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


class TestPageSize:
    """``page_size`` reaches the client, which asks the API for that limit."""

    def test_the_argument_reaches_the_client(self) -> None:
        connector = BCRAConnector(page_size=10)
        assert connector._http.config.max_page_size == 10
        with patch.object(
            connector._http, "request", return_value={"results": []}
        ) as mock_req:
            connector.monetarias.list()
        assert mock_req.call_args.args[1]["Limit"] == 10
