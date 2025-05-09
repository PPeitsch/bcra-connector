"""Integration tests focusing on error handling scenarios."""

import json
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
            rate_limit=RateLimitConfig(calls=5, period=1.0, _burst=10),
            debug=True,
        )

    @pytest.fixture
    def strict_rate_limit_connector(self) -> BCRAConnector:
        """Create a connector with strict rate limiting for testing."""
        return BCRAConnector(
            verify_ssl=False,
            rate_limit=RateLimitConfig(calls=1, period=2.0, _burst=1),
            debug=True,
        )

    def test_timeout_handling(self, short_timeout_connector: BCRAConnector) -> None:
        """Test handling of request timeouts when calling a v3.0 endpoint."""
        with pytest.raises(BCRAApiError) as exc_info:
            short_timeout_connector.get_principales_variables()
        assert "request timed out" in str(exc_info.value).lower()

    def test_connection_error(self) -> None:
        """Test handling of connection errors when calling a v3.0 endpoint."""
        connector = BCRAConnector(
            verify_ssl=False,
            timeout=TimeoutConfig(connect=0.1, read=0.1),
            rate_limit=RateLimitConfig(calls=5, period=1.0),
        )
        connector.BASE_URL = "https://nonexistent.invalid.domain.for.test"

        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_principales_variables()
        assert "connection error" in str(exc_info.value).lower()

    def test_invalid_date_range_client_validation(
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test client-side handling of invalid date ranges for get_datos_variable (v3.0)."""
        earlier_date = datetime.now() - timedelta(days=1)
        later_date = datetime.now()

        with pytest.raises(
            ValueError,
            match="'desde' date must be earlier than or equal to 'hasta' date",
        ):
            strict_rate_limit_connector.get_datos_variable(
                id_variable=1, desde=later_date, hasta=earlier_date
            )

    def test_invalid_variable_id_api_error(
        self, strict_rate_limit_connector: BCRAConnector
    ) -> None:
        """Test API error for invalid variable ID with get_datos_variable (v3.0)."""
        non_existent_id = 9999999
        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_datos_variable(
                id_variable=non_existent_id,
                desde=datetime.now() - timedelta(days=1),
                hasta=datetime.now(),
                limit=10,
            )
        error_str = str(exc_info.value).lower()
        assert (
            "resource not found (404)" in error_str
            or "idvariable invalida" in error_str
            or "400" in error_str
        )

    def test_malformed_response_handling(
        self,
        strict_rate_limit_connector: BCRAConnector,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of malformed JSON API responses from a v3.0 endpoint."""

        def mock_get_malformed_json(*args: Any, **kwargs: Any) -> requests.Response:
            response = requests.Response()
            response.status_code = 200
            response._content = b"this is not valid json {["
            response.url = "mocked_url_malformed"
            return response

        monkeypatch.setattr(
            strict_rate_limit_connector.session, "get", mock_get_malformed_json
        )

        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_principales_variables()
        assert (
            "invalid json response" in str(exc_info.value).lower()
            or "expecting value" in str(exc_info.value).lower()
        )

    def test_ssl_verification_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SSL verification error behavior when verify_ssl=True."""
        ssl_connector = BCRAConnector(
            verify_ssl=True, rate_limit=RateLimitConfig(calls=5, period=1.0)
        )

        def mock_get_ssl_error(*args: Any, **kwargs: Any) -> None:
            raise requests.exceptions.SSLError(
                "Simulated SSL verification failed (e.g., bad certificate)"
            )

        monkeypatch.setattr(ssl_connector.session, "get", mock_get_ssl_error)

        with pytest.raises(BCRAApiError) as exc_info:
            ssl_connector.get_principales_variables()
        assert (
            "ssl issue" in str(exc_info.value).lower()
            or "ssl verification failed" in str(exc_info.value).lower()
        )

    def test_retry_mechanism_for_v3_endpoint(
        self,
        strict_rate_limit_connector: BCRAConnector,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test retry mechanism for failed requests on a v3.0 endpoint."""
        failure_count = 0
        successful_v3_response_content = json.dumps({"results": []}).encode()

        def mock_request_with_retries(*args: Any, **kwargs: Any) -> requests.Response:
            nonlocal failure_count
            failure_count += 1
            if failure_count < strict_rate_limit_connector.MAX_RETRIES:
                raise requests.ConnectionError(
                    "Simulated connection failure for retry test"
                )

            # Success on the last attempt
            response = requests.Response()
            response.status_code = 200
            response._content = successful_v3_response_content
            response.url = "mocked_url_retry_success"
            return response

        connector_for_retry = BCRAConnector(
            verify_ssl=False, rate_limit=RateLimitConfig(calls=10, period=1.0)
        )
        monkeypatch.setattr(
            connector_for_retry.session, "get", mock_request_with_retries
        )

        result: List[Any] = connector_for_retry.get_principales_variables()
        assert result == []
        assert failure_count == connector_for_retry.MAX_RETRIES

    def test_various_network_errors_on_v3_endpoint(
        self,
        strict_rate_limit_connector: BCRAConnector,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of various underlying requests exceptions for a v3.0 endpoint."""
        # Test ConnectionError and Timeout specifically based on how _make_request handles them
        errors_and_expected_substrings = [
            (
                requests.ConnectionError("Simulated connection refused"),
                "connection error",
            ),
            (requests.Timeout("Simulated request timed out"), "timed out"),
            # (requests.TooManyRedirects("Simulated too many redirects"), "request failed") # Example for generic
        ]

        for error_to_simulate, expected_substring in errors_and_expected_substrings:

            def mock_network_error(*args: Any, **kwargs: Any) -> None:
                raise error_to_simulate

            monkeypatch.setattr(
                strict_rate_limit_connector.session, "get", mock_network_error
            )

            strict_rate_limit_connector.logger.info(
                f"Simulating error: {type(error_to_simulate).__name__}"
            )
            with pytest.raises(BCRAApiError) as exc_info:
                strict_rate_limit_connector.get_principales_variables()

            final_error_message = str(exc_info.value).lower()
            strict_rate_limit_connector.logger.info(
                f"Caught exception: {final_error_message}"
            )

            assert expected_substring in final_error_message
            # Optionally, also assert the generic "api request failed" for non-timeout retried errors
            if not isinstance(error_to_simulate, requests.Timeout):
                assert "api request failed" in final_error_message

    @pytest.mark.parametrize(
        "status_code, response_content, expected_match_in_exception",
        [
            (
                404,
                {"errorMessages": ["Variable no encontrada"]},
                "resource not found (404)",
            ),
            (429, {"errorMessages": ["Rate limit exceeded by server"]}, "http 429"),
            (400, {"errorMessages": ["Invalid parameter supplied"]}, "http 400"),
            (500, {"errorMessages": ["Internal BCRA server error"]}, "http 500"),
            (503, {"errorMessages": ["Service temporarily unavailable"]}, "http 503"),
        ],
    )
    def test_http_error_codes_on_v3_endpoint(
        self,
        strict_rate_limit_connector: BCRAConnector,
        status_code: int,
        response_content: Dict[str, Any],
        expected_match_in_exception: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of various HTTP error codes from a v3.0 endpoint."""

        def mock_http_error_response(*args: Any, **kwargs: Any) -> requests.Response:
            response = requests.Response()
            response.status_code = status_code
            response._content = json.dumps(response_content).encode()
            response.url = f"mocked_url_status_{status_code}"
            if status_code >= 400:
                response.reason = (
                    response_content.get("errorMessages", ["Unknown Error"])[0]
                    if response_content.get("errorMessages")
                    else "Mocked Error"
                )
                raise requests.HTTPError(response=response)
            return response

        monkeypatch.setattr(
            strict_rate_limit_connector.session, "get", mock_http_error_response
        )

        with pytest.raises(BCRAApiError) as exc_info:
            strict_rate_limit_connector.get_principales_variables()

        assert expected_match_in_exception.lower() in str(exc_info.value).lower()
        if "errorMessages" in response_content and response_content["errorMessages"]:
            assert (
                response_content["errorMessages"][0].lower()
                in str(exc_info.value).lower()
            )
