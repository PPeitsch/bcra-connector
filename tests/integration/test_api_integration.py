"""Integration tests for BCRA API endpoints."""

from datetime import date, datetime, timedelta
from typing import List, Optional

import pytest

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Cheque, Entidad
from bcra_connector.estadisticas_cambiarias import CotizacionFecha, Divisa
from bcra_connector.principales_variables import DatosVariable, PrincipalesVariables
from bcra_connector.rate_limiter import RateLimitConfig


@pytest.mark.integration
class TestBCRAIntegration:
    """Integration test suite for BCRA API."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test environment."""
        self.connector = BCRAConnector(
            verify_ssl=False,
            rate_limit=RateLimitConfig(calls=5, period=1.0),  # Conservative rate limit
        )

    def test_get_principales_variables(self) -> None:
        """Test retrieval of principal variables."""
        variables: List[PrincipalesVariables] = (
            self.connector.get_principales_variables()
        )

        assert len(variables) > 0
        assert all(isinstance(v, PrincipalesVariables) for v in variables)
        assert all(v.idVariable > 0 for v in variables)
        assert all(v.fecha is not None for v in variables)

    def test_get_historical_data(self) -> None:
        """Test retrieval of historical data for a variable."""
        # First get variables to find a valid ID
        variables: List[PrincipalesVariables] = (
            self.connector.get_principales_variables()
        )
        if not variables:
            pytest.skip("No variables available for testing")

        variable_id: int = variables[0].idVariable
        end_date: datetime = datetime.now()
        start_date: datetime = end_date - timedelta(days=30)

        data: List[DatosVariable] = self.connector.get_datos_variable(
            variable_id, start_date, end_date
        )

        assert len(data) > 0
        assert all(isinstance(d, DatosVariable) for d in data)
        assert all(start_date.date() <= d.fecha <= end_date.date() for d in data)

    def test_get_currencies(self) -> None:
        """Test retrieval of available currencies."""
        currencies: List[Divisa] = self.connector.get_divisas()

        assert len(currencies) > 0
        assert any(c.codigo == "USD" for c in currencies)
        assert all(isinstance(c, Divisa) for c in currencies)

    def test_get_exchange_rates(self) -> None:
        """Test retrieval of exchange rates."""
        rates: CotizacionFecha = self.connector.get_cotizaciones()

        assert rates is not None
        assert len(rates.detalle) > 0
        assert any(d.codigo_moneda == "USD" for d in rates.detalle)

    def test_get_financial_entities(self) -> None:
        """Test retrieval of financial entities."""
        entities: List[Entidad] = self.connector.get_entidades()

        assert len(entities) > 0
        assert all(isinstance(e, Entidad) for e in entities)
        assert all(e.codigo_entidad > 0 for e in entities)

    def test_complete_variable_workflow(self) -> None:
        """Test complete workflow for variables data."""
        # 1. Get list of variables
        variables: List[PrincipalesVariables] = (
            self.connector.get_principales_variables()
        )
        assert len(variables) > 0

        # 2. Get details for first variable
        variable: PrincipalesVariables = variables[0]
        variable_id: int = variable.idVariable

        # 3. Get historical data
        end_date: datetime = datetime.now()
        start_date: datetime = end_date - timedelta(days=30)
        historical_data: List[DatosVariable] = self.connector.get_datos_variable(
            variable_id, start_date, end_date
        )
        assert len(historical_data) > 0

        # 4. Get latest value
        latest_value: DatosVariable = self.connector.get_latest_value(variable_id)
        assert latest_value is not None
        assert latest_value.fecha <= end_date.date()

    def test_currency_evolution(self) -> None:
        """Test currency evolution over time."""
        # Get USD evolution for last month
        evolution: List[CotizacionFecha] = self.connector.get_evolucion_moneda(
            "USD", limit=30
        )

        assert len(evolution) > 0
        assert all(isinstance(cf, CotizacionFecha) for cf in evolution)
        assert all(
            any(d.codigo_moneda == "USD" for d in cf.detalle) for cf in evolution
        )

    @pytest.mark.skip(reason="Requires valid check data")
    def test_check_verification(self) -> None:
        """Test check verification workflow."""
        # This test requires valid check data
        entities: List[Entidad] = self.connector.get_entidades()
        if not entities:
            pytest.skip("No entities available for testing")

        entity: Entidad = entities[0]
        try:
            check: Optional[Cheque] = self.connector.get_cheque_denunciado(
                entity.codigo_entidad, 12345  # Example check number
            )
            assert check is not None
            assert isinstance(check.denunciado, bool)
        except BCRAApiError as e:
            if "404" in str(e):
                pytest.skip("No check data available")
            raise

    def test_error_handling(self) -> None:
        """Test API error handling."""
        with pytest.raises(BCRAApiError):
            # Try to get data for non-existent variable
            self.connector.get_datos_variable(
                99999, datetime.now() - timedelta(days=1), datetime.now()
            )

    @pytest.mark.skip(reason="Long running test")
    def test_rate_limit_compliance(self) -> None:
        """Test rate limit compliance over multiple requests."""
        start_time: float = datetime.now().timestamp()
        request_count: int = 15  # More than our rate limit

        for _ in range(request_count):
            self.connector.get_principales_variables()

        elapsed: float = datetime.now().timestamp() - start_time
        requests_per_second: float = request_count / elapsed

        # Should respect our rate limit of 5 requests per second
        assert requests_per_second <= 5
