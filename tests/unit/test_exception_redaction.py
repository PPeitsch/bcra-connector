"""Exceptions never carry the unmasked CUIT/CUIL (#169).

Every error path of ``HttpClient.request()`` builds its message from the URL or from
the ``requests`` exception, and both contain the identifier. The message must carry
only its masked form, and no ``requests`` exception may be chained to it: a logged
traceback or an error tracker would print that one's message too.
"""

import json
import traceback
from typing import Union
from unittest.mock import Mock, patch

import pytest
import requests

from bcra_connector import (
    BCRAApiError,
    BCRAConnector,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
    RateLimitConfig,
)

CUIT = "30712345672"
MASKED = "30********2"
ENDPOINT = f"CentralDeDeudores/v1.0/Deudas/{CUIT}"
URL = f"https://api.bcra.gob.ar/{ENDPOINT}"


def _http_error(status: int) -> Mock:
    response = Mock()
    response.headers = {}
    response.status_code = status
    response.url = URL
    response.reason = "Reason"
    # The API echoes the identifier in some error bodies.
    response.json.return_value = {"errorMessages": [f"Sin datos para {CUIT}"]}
    response.raise_for_status.side_effect = requests.HTTPError(
        f"{status} Error for url: {URL}", response=response
    )
    return response


def _bad_json(error: Exception) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = error
    return response


CASES = {
    "404": (lambda: _http_error(404), BCRANotFoundError),
    "429 after retries": (lambda: _http_error(429), BCRARateLimitError),
    "5xx after retries": (lambda: _http_error(503), BCRAServerError),
    "other 4xx": (lambda: _http_error(400), BCRAApiError),
    "timeout": (
        lambda: requests.Timeout(f"Read timed out. (url: {URL})"),
        BCRAApiError,
    ),
    "SSL": (
        lambda: requests.exceptions.SSLError(f"SSL: CERTIFICATE_VERIFY_FAILED ({URL})"),
        BCRAApiError,
    ),
    "connection": (
        lambda: requests.ConnectionError(f"Max retries exceeded ({URL})"),
        BCRAApiError,
    ),
    "other requests error": (
        lambda: requests.TooManyRedirects(f"Exceeded 30 redirects: {URL}"),
        BCRAApiError,
    ),
    "invalid JSON": (
        lambda: _bad_json(json.JSONDecodeError("Expecting value", "", 0)),
        BCRAApiError,
    ),
    # What ``response.json()`` really raises: it is also a RequestException, so
    # today it takes the generic path (retried) instead of "Invalid JSON".
    "invalid JSON (requests)": (
        lambda: _bad_json(
            requests.exceptions.JSONDecodeError("Expecting value", "", 0)
        ),
        BCRAApiError,
    ),
}


def _error_from(outcome: Union[Mock, Exception], retries: int = 3) -> BCRAApiError:
    """Run a request whose ``session.get`` returns ``outcome`` or raises it."""
    connector = BCRAConnector(
        retries=retries, rate_limit=RateLimitConfig(calls=1000, period=1.0)
    )
    get = (
        Mock(side_effect=outcome)
        if isinstance(outcome, Exception)
        else Mock(return_value=outcome)
    )
    with (
        patch.object(connector.session, "get", get),
        patch("bcra_connector._http.time.sleep"),
        pytest.raises(BCRAApiError) as excinfo,
    ):
        connector._make_request(ENDPOINT)
    return excinfo.value


def _assert_masked(error: BCRAApiError) -> None:
    assert CUIT not in str(error)
    assert MASKED in str(error)
    assert error.__cause__ is None
    assert error.__context__ is None
    assert CUIT not in "".join(traceback.format_exception(error))


@pytest.mark.parametrize("case", list(CASES))
def test_error_paths_mask_the_identifier(case: str) -> None:
    make, expected = CASES[case]

    error = _error_from(make())

    assert type(error) is expected
    _assert_masked(error)


def test_the_error_body_is_masked_too() -> None:
    error = _error_from(_http_error(404))

    assert f"Sin datos para {MASKED}" in str(error)


def test_zero_retries_reports_the_masked_url() -> None:
    """With no attempts at all, the fallback message still masks the URL."""
    error = _error_from(Mock(), retries=0)

    assert "Maximum retry attempts (0)" in str(error)
    _assert_masked(error)


@pytest.mark.parametrize("status", [404, 429, 503, 400])
def test_status_code_survives_without_the_chain(status: int) -> None:
    """Dropping the chained exception loses nothing callers rely on."""
    assert _error_from(_http_error(status)).status_code == status
