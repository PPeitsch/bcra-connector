"""
Integration tests for Central de Deudores API.

These tests run against the live BCRA API and require network access.
Note: Queries require valid CUIT/CUIL/CDI numbers.
Most test CUITs will return 404 "not found" responses.
"""

import pytest

from bcra_connector import BCRAApiError, BCRAConnector


@pytest.fixture
def connector() -> BCRAConnector:
    """Create a BCRAConnector instance for testing."""
    return BCRAConnector()


class TestCentralDeDeudoresIntegration:
    """Integration tests for Central de Deudores API."""

    # Test CUIT - this is a sample that likely returns 404
    # Real integration tests would need a valid CUIT with data
    TEST_CUIT = "20000000007"  # Sample test CUIT

    @pytest.mark.integration
    def test_get_deudas_not_found(self, connector: BCRAConnector) -> None:
        """Test that querying unknown CUIT returns appropriate error."""
        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_deudas(self.TEST_CUIT)
        # API returns 404 for unknown CUITs
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_get_deudas_historicas_not_found(self, connector: BCRAConnector) -> None:
        """Test that querying unknown CUIT for historical debts returns error."""
        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_deudas_historicas(self.TEST_CUIT)
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_get_cheques_rechazados_not_found(self, connector: BCRAConnector) -> None:
        """Test that querying unknown CUIT for rejected checks returns error."""
        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_cheques_rechazados(self.TEST_CUIT)
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_get_deudas_invalid_cuit_length(self, connector: BCRAConnector) -> None:
        """Test validation of CUIT length before API call."""
        with pytest.raises(ValueError, match="exactly 11 digits"):
            connector.get_deudas("12345")

    @pytest.mark.integration
    def test_get_deudas_strips_formatting(self, connector: BCRAConnector) -> None:
        """Test that formatted CUIT is properly handled."""
        # This should not raise ValueError - it should strip formatting
        # and then hit the API (which will return 404)
        with pytest.raises(BCRAApiError):
            connector.get_deudas("20-00000000-7")
