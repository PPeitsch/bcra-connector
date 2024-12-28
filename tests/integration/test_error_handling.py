"""Integration tests focusing on error handling scenarios."""

import json
import ssl
import time
from datetime import datetime, timedelta
from typing import Any

import pytest
import requests

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.rate_limiter import RateLimitConfig
from bcra_connector.timeout_config import TimeoutConfig


@pytest.mark.integration
class TestErrorHandling:
    """Integration test suite for error handling scenarios."""

    @pytest.fixture
    def short_timeout_connector(self) -> BCRAConnector:
        """Create a connector with very short timeouts."""
        timeout_config = TimeoutConfig(connect=0.001, read=0.001)
        return BCRAConnector(
            verify_ssl=False,
            timeout=timeout_config,
            rate_limit=RateLimitConfig(calls=5, period=1.0),
        )

    @pytest.fixture
    def strict_rate_limit_connector(self) -> BCRAConnector:
        """Create a connector with strict rate limiting."""
        return BCRAConnector(
            verify_ssl=False, rate_limit=RateLimitConfig(calls=1, period=2.0)
        )

    def test_timeout_handling(self, short_timeout_connector: BCRAConnector) -> None:
        """Test handling of request timeouts."""
        with pytest.raises(BCRAApiError) as exc_info:
            short_timeout_connector.get_principales_variables()
        assert "request timed out" in str(exc_info.value).lower()

    def test_connection_error(self) -> None:
        """Test handling of connection errors."""
        connector = BCRAConnector(
            verify_ssl=False, timeout=TimeoutConfig(connect=0.1, read=0.1)
        )
        connector.BASE_URL = "https://nonexistent.example.com"

        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_principales_variables()
        assert "connection error" in str(exc_info.value).lower()

    def test_invalid_date_range(
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test handling of invalid date ranges."""
        future_date = datetime.now() + timedelta(days=30)
        past_date = datetime.now() - timedelta(days=400)  # Beyond allowed range

        with pytest.raises(ValueError) as exc_info:
            strict_rate_limit_connector.get_datos_variable(
                1, future_date, datetime.now()
            )
        assert "date" in str(exc_info.value).lower()

        with pytest.raises(ValueError) as exc_info:
            strict_rate_limit_connector.get_datos_variable(1, past_date, datetime.now())
        assert "range" in str(exc_info.value).lower()

    def test_invalid_variable_id(
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test handling of invalid variable IDs."""
        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_datos_variable(
                999999, datetime.now() - timedelta(days=1), datetime.now()  # Invalid ID
            )
        assert (
            "404" in str(exc_info.value)
            or "not found" in str(exc_info.value).lower()
            or "400" in str(exc_info.value)
        )

    def test_malformed_response_handling(
        self,
        strict_rate_limit_connector: BCRAConnector,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of malformed API responses."""

        def mock_get(*args: Any, **kwargs: Any) -> requests.Response:
            response = requests.Response()
            response.status_code = 200
            response._content = b"invalid json{{"
            return response

        monkeypatch.setattr(strict_rate_limit_connector.session, "get", mock_get)

        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_principales_variables()
        assert "invalid json" in str(exc_info.value).lower()

    def test_ssl_verification(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SSL verification behavior."""
        connector = BCRAConnector(verify_ssl=True)

        def mock_get(*args: Any, **kwargs: Any) -> None:
            raise ssl.SSLError("SSL verification failed")

        monkeypatch.setattr(connector.session, "get", mock_get)

        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_principales_variables()
        assert "ssl verification failed" in str(exc_info.value).lower()

    def test_retry_mechanism(
        self,
        strict_rate_limit_connector: BCRAConnector,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test retry mechanism for failed requests."""
        failure_count = 0

        def mock_request(*args: Any, **kwargs: Any) -> requests.Response:
            nonlocal failure_count
            failure_count += 1
            if failure_count < 3:
                raise requests.ConnectionError("Simulated connection failure")

            response = requests.Response()
            response.status_code = 200
            response._content = b'{"results": []}'
            return response

        # Reset rate limiter before test
        strict_rate_limit_connector.rate_limiter.reset()
        strict_rate_limit_connector.rate_limiter.config = RateLimitConfig(
            calls=3, period=1.0, _burst=3
        )
        monkeypatch.setattr(strict_rate_limit_connector.session, "get", mock_request)

        result = strict_rate_limit_connector.get_principales_variables()
        assert result == []
        assert failure_count == 3  # Two failures + one success

    def test_network_errors(
        self,
        strict_rate_limit_connector: BCRAConnector,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of various network errors."""
        for error in [
            requests.ConnectionError("Connection refused"),
            requests.Timeout("Request timed out"),
            requests.TooManyRedirects("Too many redirects"),
        ]:

            def mock_error(*args: Any, **kwargs: Any) -> None:
                raise error

            monkeypatch.setattr(strict_rate_limit_connector.session, "get", mock_error)

            with pytest.raises(BCRAApiError):
                strict_rate_limit_connector.get_principales_variables()

    @pytest.mark.parametrize(
        "status_code,expected_message",
        [
            (404, "HTTP 404: Resource not found"),
            (429, "HTTP 429: Rate limit exceeded"),
            (400, "HTTP 400"),
            (500, "HTTP 500"),
        ],
    )
    def test_http_error_codes(
        self,
        strict_rate_limit_connector: BCRAConnector,
        status_code: int,
        expected_message: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of various HTTP error codes."""

        def mock_get(*args: Any, **kwargs: Any) -> requests.Response:
            response = requests.Response()
            response.status_code = status_code
            response._content = json.dumps(
                {"errorMessages": [f"Test error for {status_code}"]}
            ).encode()
            response.url = "test_url"
            return response

        monkeypatch.setattr(strict_rate_limit_connector.session, "get", mock_get)

        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_principales_variables()

        assert f"http {status_code}" in str(exc_info.value).lower()
