"""Integration tests focusing on error handling scenarios."""

import json
import socket
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

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
        assert "timeout" in str(exc_info.value).lower()

    def test_connection_error(self) -> None:
        """Test handling of connection errors."""
        connector = BCRAConnector(
            verify_ssl=False,
            timeout=TimeoutConfig(connect=0.1, read=0.1)
        )
        connector.BASE_URL = "https://nonexistent.example.com"

        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_principales_variables()
        assert "connection error" in str(exc_info.value).lower()

    def test_rate_limit_exceeded(
            self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test handling of rate limit exceeded."""
        strict_rate_limit_connector.rate_limiter.config = RateLimitConfig(
            calls=1, period=1.0, _burst=1
        )

        strict_rate_limit_connector.get_principales_variables()

        start_time = time.monotonic()
        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_principales_variables()
        duration = time.monotonic() - start_time

        assert duration >= 1.0
        assert "rate limit" in str(exc_info.value).lower()

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
            "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
        )

    def test_malformed_response_handling(
            self, strict_rate_limit_connector: BCRAConnector, monkeypatch: pytest.MonkeyPatch
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

    def test_ssl_verification(self) -> None:
        """Test SSL verification behavior."""
        strict_connector = BCRAConnector(verify_ssl=True)
        lenient_connector = BCRAConnector(verify_ssl=False)

        # Both should work with valid SSL
        strict_result = strict_connector.get_principales_variables()
        lenient_result = lenient_connector.get_principales_variables()

        assert len(strict_result) == len(lenient_result)

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
                raise requests.ConnectionError("Simulated failure")
            response = requests.Response()
            response.status_code = 200
            response._content = b'{"results": []}'
            return response

        monkeypatch.setattr(strict_rate_limit_connector.session, "get", mock_request)
        result = strict_rate_limit_connector.get_principales_variables()
        assert result is not None
        assert failure_count == 3  # Two failures + one success

    def test_network_errors(self, strict_rate_limit_connector: BCRAConnector) -> None:
        """Test handling of various network errors."""
        errors = [
            requests.ConnectionError("Connection refused"),
            requests.Timeout("Request timed out"),
            socket.gaierror("Name resolution error"),
            requests.TooManyRedirects("Too many redirects"),
            requests.RequestException("Generic request error"),
        ]

        for error in errors:
            with pytest.raises(BCRAApiError):
                # Simulate each type of error
                with pytest.raises(type(error)):
                    raise error

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 500, 502, 503])
    def test_http_error_codes(
            self, strict_rate_limit_connector: BCRAConnector, status_code: int
    ) -> None:
        """Test handling of various HTTP error codes."""

        def mock_get(*args: Any, **kwargs: Any) -> requests.Response:
            response = requests.Response()
            response.status_code = status_code
            response._content = json.dumps({
                "errorMessages": [f"Test error for {status_code}"]
            }).encode()
            response.url = "test_url"
            response.reason = f"Error {status_code}"
            return response

        with patch.object(strict_rate_limit_connector.session, "get", mock_get):
            with pytest.raises(BCRAApiError) as exc_info:
                strict_rate_limit_connector.get_principales_variables()

            error_msg = str(exc_info.value).lower()
            if status_code == 404:
                assert "not found" in error_msg
            else:
                assert str(status_code) in error_msg
