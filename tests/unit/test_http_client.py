"""Session injection and the transport knobs after the HttpClient extraction."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

from bcra_connector import BCRAConnector


def _ok_response() -> Mock:
    response = Mock()
    response.json.return_value = {"results": []}
    return response


def _error_response(status: int = 503) -> Mock:
    response = Mock()
    response.status_code = status
    response.url = "https://api.bcra.gob.ar/test"
    response.reason = "Service Unavailable"
    response.json.return_value = {"errorMessages": ["nope"]}
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    return response


class TestInjectedSession:
    def test_requests_go_through_it(self) -> None:
        session = requests.Session()
        connector = BCRAConnector(session=session)
        assert connector.session is session
        with patch.object(session, "get", return_value=_ok_response()) as mock_get:
            connector._make_request("test")
        assert mock_get.call_count == 1

    def test_headers_are_set_on_it(self) -> None:
        session = requests.Session()
        BCRAConnector(language="en-US", session=session)
        assert session.headers["Accept-Language"] == "en-US"
        assert session.headers["User-Agent"].startswith("bcra-connector/")

    def test_close_leaves_an_injected_session_open(self) -> None:
        session = requests.Session()
        with patch.object(session, "close") as mock_close:
            with BCRAConnector(session=session):
                pass
        mock_close.assert_not_called()

    def test_close_closes_an_owned_session(self) -> None:
        connector = BCRAConnector()
        with patch.object(connector.session, "close") as mock_close:
            connector.close()
        mock_close.assert_called_once()


class TestTransportKnobs:
    """The knobs stay class attributes: subclassing and assignment keep working."""

    def _attempts(self, connector: BCRAConnector) -> int:
        with (
            patch.object(
                connector.session, "get", return_value=_error_response()
            ) as mock_get,
            patch("bcra_connector._http.time.sleep"),
            pytest.raises(Exception),
        ):
            connector._make_request("test")
        return int(mock_get.call_count)

    def test_instance_assignment_is_honoured(self) -> None:
        connector = BCRAConnector()
        assert self._attempts(connector) == 3
        connector.MAX_RETRIES = 1
        assert self._attempts(connector) == 1

    def test_subclass_override_is_honoured(self) -> None:
        class Patient(BCRAConnector):
            MAX_RETRIES = 5

        assert self._attempts(Patient()) == 5

    def test_base_url_is_read_per_request(self) -> None:
        connector = BCRAConnector()
        connector.BASE_URL = "https://example.invalid"
        with patch.object(
            connector.session, "get", return_value=_ok_response()
        ) as mock_get:
            connector._make_request("some/endpoint")
        assert mock_get.call_args.args[0] == "https://example.invalid/some/endpoint"

    def test_class_level_read_still_works(self) -> None:
        # e.g. BCRAConnector.RETRY_DELAY, used by callers and tests
        assert BCRAConnector.MAX_RETRIES == 3
        assert BCRAConnector.RETRY_DELAY == 1
        assert BCRAConnector.CATALOG_CACHE_TTL == 300.0


class TestDelegation:
    def test_connector_shares_the_clients_objects(self) -> None:
        connector = BCRAConnector()
        assert connector.session is connector._http.session
        assert connector.timeout is connector._http.timeout
        assert connector.rate_limiter is connector._http.rate_limiter
        assert connector.verify_ssl == connector._http.verify_ssl

    def test_assigning_a_session_reaches_the_client(self) -> None:
        # 0.12 allowed replacing the session after construction; it still works.
        connector = BCRAConnector()
        replacement = requests.Session()
        connector.session = replacement
        assert connector._http.session is replacement
        with patch.object(
            replacement, "get", return_value=_ok_response()
        ) as mock_get:
            connector._make_request("test")
        assert mock_get.call_count == 1

    def test_clear_cache_reaches_the_client(self) -> None:
        connector = BCRAConnector()
        loader: Any = Mock(return_value=["x"])
        connector._cached("k", loader)
        connector._cached("k", loader)
        assert loader.call_count == 1
        connector.clear_cache()
        connector._cached("k", loader)
        assert loader.call_count == 2
