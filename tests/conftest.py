import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_api_response():
    """Fixture to simulate API responses."""

    def _mock_response(data, status_code=200):
        response = Mock()
        response.json.return_value = data
        response.status_code = status_code
        return response

    return _mock_response


@pytest.fixture
def sample_variable_data():
    """Fixture with sample variable data."""
    return {
        "idVariable": 1,
        "cdSerie": 246,
        "descripcion": "Test Variable",
        "fecha": "2024-03-05",
        "valor": 100.0
    }


@pytest.fixture
def bcra_connector():
    """Fixture for BCRAConnector instance."""
    from bcra_connector import BCRAConnector
    return BCRAConnector(verify_ssl=False)
