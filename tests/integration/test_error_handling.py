"""Integration tests focusing on error handling scenarios."""

import json
import socket
from datetime import datetime, timedelta
from typing import Any, Dict, List

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
        connector = BCRAConnector(base_url="https://invalid.bcra.ar")

        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_principales_variables()

        error_msg = str(exc_info.value).lower()
        assert any(
            term in error_msg for term in ["connection", "dns", "timeout", "refused"]
        )

    def test_rate_limit_exceeded(
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test handling of rate limit exceeded."""
        # Make rapid successive requests
        strict_rate_limit_connector.get_principales_variables()

        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_principales_variables()

        error = str(exc_info.value).lower()
        assert any(term in error for term in ["rate limit", "too many requests", "429"])

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
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test handling of malformed API responses."""
        with pytest.raises(BCRAApiError) as exc_info:
            # Force malformed JSON response
            with pytest.raises(json.JSONDecodeError):
                strict_rate_limit_connector._make_request("invalid/endpoint")

        assert any(
            term in str(exc_info.value).lower()
            for term in ["invalid", "malformed", "error"]
        )

    def test_ssl_verification(self) -> None:
        """Test SSL verification behavior."""
        strict_connector = BCRAConnector(verify_ssl=True)
        lenient_connector = BCRAConnector(verify_ssl=False)

        # Both should work with valid SSL
        strict_result = strict_connector.get_principales_variables()
        lenient_result = lenient_connector.get_principales_variables()

        assert len(strict_result) == len(lenient_result)

    def test_retry_mechanism(self, strict_rate_limit_connector: BCRAConnector) -> None:
        """Test retry mechanism for failed requests."""
        original_make_request = strict_rate_limit_connector._make_request

        failure_count = 0

        def mock_make_request(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            nonlocal failure_count
            failure_count += 1
            if failure_count < 3:
                raise requests.ConnectionError("Simulated failure")
            return original_make_request(*args, **kwargs)

        strict_rate_limit_connector._make_request = mock_make_request  # type: ignore

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

    def test_response_validation(
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test validation of API responses."""
        # Test missing required fields
        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector._handle_response({})
        assert "unexpected" in str(exc_info.value).lower()

        # Test invalid data types
        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector._handle_response(
                {"results": "not a list or dict"}
            )
        assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 500, 502, 503])
    def test_http_error_codes(
        self, strict_rate_limit_connector: BCRAConnector, status_code: int
    ) -> None:
        """Test handling of various HTTP error codes."""
        with pytest.raises(BCRAApiError) as exc_info:
            response = requests.Response()
            response.status_code = status_code
            strict_rate_limit_connector._handle_error_response(response)

        assert str(status_code) in str(exc_info.value)
