"""Tests for the monetarias sub-client."""

from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


class TestPageSize:
    """The catalog page size still comes from the class attribute (until 1.0)."""

    def test_subclass_override_reaches_the_client(self) -> None:
        class Small(BCRAConnector):
            MAX_PAGE_SIZE = 10

        connector = Small()
        assert connector._http.config().max_page_size == 10
        with patch.object(
            connector._http, "request", return_value={"results": []}
        ) as mock_req:
            connector.monetarias.list()
        assert mock_req.call_args.args[1]["Limit"] == 10
