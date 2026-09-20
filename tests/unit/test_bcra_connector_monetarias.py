"""Tests for the monetarias sub-client and its deprecated aliases."""

from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector()


class TestDeprecatedAliases:
    """The old connector methods delegate and warn until 1.0."""

    @pytest.mark.parametrize(
        "old,new,args",
        [
            ("get_principales_variables", "list", ()),
            (
                "get_datos_variable",
                "series",
                (1, datetime(2024, 1, 1), datetime(2024, 1, 2), 10, 0),
            ),
            ("get_latest_value", "latest", (1,)),
            ("get_variable_by_name", "find", ("Reservas",)),
            ("get_variable_history", "history", ("Reservas", 10, 20, 0)),
        ],
    )
    def test_alias_warns_and_delegates(
        self, connector: BCRAConnector, old: str, new: str, args: Any
    ) -> None:
        sentinel = object()
        with patch.object(
            connector.monetarias, new, return_value=sentinel
        ) as mock_method:
            with pytest.warns(DeprecationWarning, match=f"monetarias.{new}"):
                result = getattr(connector, old)(*args)
        mock_method.assert_called_once_with(*args)
        assert result is sentinel


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
