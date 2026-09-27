"""Session injection and the transport knobs after the HttpClient extraction."""

import logging
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
import requests
from requests.structures import CaseInsensitiveDict

from bcra_connector import BCRAConnector, RateLimitConfig


def _ok_response() -> Mock:
    response = Mock()
    response.json.return_value = {"results": []}
    return response


def _error_response(status: int = 503) -> Mock:
    response = Mock()
    response.headers = {}
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
        assert str(session.headers["User-Agent"]).startswith("bcra-connector/")

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
    """The knobs are constructor arguments; each one reaches the transport."""

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

    def test_retries_defaults_to_three(self) -> None:
        assert self._attempts(BCRAConnector()) == 3

    @pytest.mark.parametrize("retries", [1, 5])
    def test_retries_is_honoured(self, retries: int) -> None:
        assert self._attempts(BCRAConnector(retries=retries)) == retries

    def test_base_url_is_used(self) -> None:
        connector = BCRAConnector(base_url="https://example.invalid")
        with patch.object(
            connector.session, "get", return_value=_ok_response()
        ) as mock_get:
            connector._make_request("some/endpoint")
        assert mock_get.call_args.args[0] == "https://example.invalid/some/endpoint"

    def test_the_defaults_are_the_documented_ones(self) -> None:
        config = BCRAConnector()._http.config

        assert config.base_url == "https://api.bcra.gob.ar"
        assert config.max_retries == 3
        assert config.retry_delay == 1
        assert config.max_retry_after == 30.0
        assert config.max_pages == 100
        assert config.cache_ttl == 300.0
        assert config.max_page_size == 3000
        assert config.fx_max_page_size == 1000

    def test_every_argument_reaches_the_transport(self) -> None:
        config = BCRAConnector(
            base_url="https://example.invalid",
            retries=7,
            retry_delay=0.5,
            max_retry_after=4,
            max_pages=9,
            cache_ttl=0,
            page_size=11,
            fx_page_size=13,
        )._http.config

        assert config.base_url == "https://example.invalid"
        assert config.max_retries == 7
        assert config.retry_delay == 0.5
        assert config.max_retry_after == 4
        assert config.max_pages == 9
        assert config.cache_ttl == 0
        assert config.max_page_size == 11
        assert config.fx_max_page_size == 13

    def test_the_config_cannot_be_mutated_after_construction(self) -> None:
        """Frozen on purpose: configuration happens once, at construction."""
        with pytest.raises(AttributeError):
            BCRAConnector()._http.config.max_retries = 1


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
        with patch.object(replacement, "get", return_value=_ok_response()) as mock_get:
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


class TestDefaultRateLimit:
    def test_is_below_the_observed_429(self) -> None:
        """The Central de Deudores answered 429 at about 5 req/s (#168)."""
        assert BCRAConnector.DEFAULT_RATE_LIMIT == RateLimitConfig(calls=2, period=1.0)


def _throttled(status: int, headers: Dict[str, str]) -> Mock:
    response = _error_response(status)
    response.headers = CaseInsensitiveDict(headers)
    return response


class TestRetryAfter:
    """A 429/503 with Retry-After waits what the server asks, up to a cap (#168)."""

    def _sleeps(
        self, first: Mock, connector: Optional[BCRAConnector] = None
    ) -> List[float]:
        connector = connector or BCRAConnector(
            rate_limit=RateLimitConfig(calls=100, period=1.0)
        )
        with (
            patch.object(connector.session, "get", side_effect=[first, _ok_response()]),
            patch("bcra_connector._http.time.sleep") as mock_sleep,
        ):
            connector._make_request("test")
        return [c.args[0] for c in mock_sleep.call_args_list]

    @pytest.mark.parametrize("status", [429, 503])
    def test_seconds(self, status: int) -> None:
        assert self._sleeps(_throttled(status, {"Retry-After": "7"})) == [7.0]

    def test_http_date(self) -> None:
        when = datetime.now(timezone.utc) + timedelta(seconds=12)
        header = format_datetime(when, usegmt=True)

        [slept] = self._sleeps(_throttled(429, {"Retry-After": header}))

        assert 10 <= slept <= 12

    def test_a_date_in_the_past_retries_right_away(self) -> None:
        header = "Wed, 21 Oct 2015 07:28:00 GMT"
        assert self._sleeps(_throttled(429, {"Retry-After": header})) == [0.0]

    def test_missing_keeps_the_backoff(self) -> None:
        assert self._sleeps(_throttled(429, {})) == [1.0]

    @pytest.mark.parametrize("header", ["soon", "-5", "1.5", ""])
    def test_unusable_keeps_the_backoff(self, header: str) -> None:
        assert self._sleeps(_throttled(429, {"Retry-After": header})) == [1.0]

    def test_above_the_cap_waits_the_cap(self) -> None:
        response = _throttled(429, {"Retry-After": "86400"})
        assert self._sleeps(response) == [30.0]

    def test_the_cap_is_configurable(self) -> None:
        connector = BCRAConnector(
            max_retry_after=5, rate_limit=RateLimitConfig(calls=100, period=1.0)
        )
        response = _throttled(503, {"Retry-After": "60"})
        assert self._sleeps(response, connector) == [5.0]

    def test_other_5xx_ignore_it(self) -> None:
        """Only 429 and 503 define Retry-After as "come back later"."""
        assert self._sleeps(_throttled(500, {"Retry-After": "7"})) == [1.0]

    def test_a_429_logs_its_headers(self, caplog: pytest.LogCaptureFixture) -> None:
        response = _throttled(
            429,
            {"Retry-After": "7", "X-RateLimit-Limit": "5", "Set-Cookie": "id=secret"},
        )
        with caplog.at_level(logging.WARNING, logger="bcra_connector"):
            self._sleeps(response)

        [record] = [r for r in caplog.records if "response headers" in r.message]
        assert "'Retry-After': '7'" in record.message
        assert "'X-RateLimit-Limit': '5'" in record.message
        assert "secret" not in record.message
