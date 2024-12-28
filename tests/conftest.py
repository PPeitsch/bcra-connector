"""Pytest configuration and shared fixtures."""

from typing import Any, Callable, Dict
from unittest.mock import Mock

import pytest

from bcra_connector import BCRAConnector


@pytest.fixture
def mock_api_response() -> Callable[[Dict[str, Any], int], Mock]:
    """Fixture to simulate API responses.

    Returns:
        Function that creates mock responses with given data and status code
    """

    def _mock_response(data: Dict[str, Any], status_code: int = 200) -> Mock:
        response = Mock()
        response.json.return_value = data
        response.status_code = status_code
        return response

    return _mock_response


@pytest.fixture
def sample_variable_data() -> Dict[str, Any]:
    """Fixture with sample variable data.

    Returns:
        Dictionary containing sample variable data
    """
    return {
        "idVariable": 1,
        "cdSerie": 246,
        "descripcion": "Test Variable",
        "fecha": "2024-03-05",
        "valor": 100.0,
    }


@pytest.fixture
def bcra_connector() -> BCRAConnector:
    """Fixture for BCRAConnector instance.

    Returns:
        Configured BCRAConnector instance for testing
    """
    return BCRAConnector(verify_ssl=False)
