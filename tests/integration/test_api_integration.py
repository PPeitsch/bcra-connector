"""Integration tests for BCRA API endpoints, including Monetarias v4.0."""

from datetime import datetime, timedelta
from typing import List

import pytest

from bcra_connector import BCRAApiError, BCRAConnector
from bcra_connector.cheques import Entidad
from bcra_connector.estadisticas_cambiarias import CotizacionFecha, Divisa
from bcra_connector.principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
from bcra_connector.rate_limiter import RateLimitConfig


@pytest.mark.integration
class TestBCRAIntegration:
    """Integration test suite for BCRA API, including Monetarias v4.0."""

    @pytest.fixture(scope="class")
    def connector(self) -> BCRAConnector:
        """Set up BCRAConnector instance for the test class."""
        return BCRAConnector(
            verify_ssl=False,
            rate_limit=RateLimitConfig(calls=3, period=1.0, _burst=5),
            debug=True,
        )

    def test_get_principales_variables_v3(self, connector: BCRAConnector) -> None:
        """Test retrieval of principal variables/monetary series (Monetarias v4.0)."""
        variables: List[PrincipalesVariables] = connector.get_principales_variables()

        assert variables, "Should retrieve a list of variables"
        assert len(variables) > 0, "Expected at least one variable"

        first_var = variables[0]
        assert isinstance(first_var, PrincipalesVariables)
        assert hasattr(first_var, "idVariable") and first_var.idVariable > 0
        assert hasattr(first_var, "descripcion") and first_var.descripcion
        # v4.0 has ultFechaInformada and ultValorInformado instead of fecha/valor
        assert hasattr(first_var, "ultFechaInformada")
        assert hasattr(first_var, "ultValorInformado")
        assert hasattr(first_var, "categoria")

    def test_get_historical_data_v3(self, connector: BCRAConnector) -> None:
        """Test retrieval of historical data for a variable (Monetarias v4.0)."""
        variables: List[PrincipalesVariables] = connector.get_principales_variables()
        if not variables:
            pytest.skip(
                "No principal variables available to test historical data retrieval."
            )

        variable_id: int = variables[0].idVariable
        variable_desc: str = variables[0].descripcion
        connector.logger.info(
            f"Testing historical data for ID: {variable_id} ({variable_desc})"
        )

        end_date: datetime = datetime.now()
        start_date: datetime = end_date - timedelta(days=7)

        response_data: DatosVariableResponse = connector.get_datos_variable(
            id_variable=variable_id, desde=start_date, hasta=end_date, limit=10
        )

        assert isinstance(response_data, DatosVariableResponse)
        assert response_data.status == 200
        assert response_data.metadata is not None
        assert response_data.metadata.resultset is not None
        assert response_data.metadata.resultset.limit == 10
        assert len(response_data.results) <= 10

        if not response_data.results:
            connector.logger.warning(
                f"No historical data found for {variable_id} in the last 7 days with limit 10."
            )
        else:
            first_data_point = response_data.results[0]
            assert isinstance(first_data_point, DatosVariable)
            assert first_data_point.idVariable == variable_id
            # v4.0 has detalle array instead of direct fecha/valor
            assert len(first_data_point.detalle) > 0
            assert all(
                isinstance(d, DetalleMonetaria) for d in first_data_point.detalle
            )

        response_offset: DatosVariableResponse = connector.get_datos_variable(
            id_variable=variable_id, limit=15, offset=5
        )
        assert response_offset.metadata.resultset.offset == 5
        assert response_offset.metadata.resultset.limit == 15

    def test_get_currencies(self, connector: BCRAConnector) -> None:
        """Test retrieval of available currencies (Estadisticas Cambiarias)."""
        currencies: List[Divisa] = connector.get_divisas()

        assert currencies, "Should retrieve a list of currencies"
        assert len(currencies) > 0
        assert any(c.codigo == "USD" for c in currencies)
        assert all(isinstance(c, Divisa) for c in currencies)

    def test_get_exchange_rates(self, connector: BCRAConnector) -> None:
        """Test retrieval of exchange rates for today or latest (Estadisticas Cambiarias)."""
        rates: CotizacionFecha = connector.get_cotizaciones()

        assert rates is not None
        assert rates.detalle is not None
        if rates.fecha is not None:
            assert rates.fecha <= datetime.now().date()

        if not rates.detalle:
            connector.logger.warning(
                "No exchange rate details found for the latest date."
            )
        else:
            assert len(rates.detalle) > 0
            assert any(d.codigo_moneda == "USD" for d in rates.detalle)

    def test_get_financial_entities(self, connector: BCRAConnector) -> None:
        """Test retrieval of financial entities (Cheques API)."""
        entities: List[Entidad] = connector.get_entidades()

        assert entities, "Should retrieve a list of financial entities"
        assert len(entities) > 0
        assert all(isinstance(e, Entidad) for e in entities)
        assert all(e.codigo_entidad > 0 for e in entities)

    def test_complete_variable_workflow_v3(self, connector: BCRAConnector) -> None:
        """Test complete workflow for Monetarias v4.0 data."""
        variables: List[PrincipalesVariables] = connector.get_principales_variables()
        assert (
            variables and len(variables) > 0
        ), "Failed to get principal variables list"

        variable: PrincipalesVariables = variables[0]
        variable_id: int = variable.idVariable
        connector.logger.info(
            f"Testing complete workflow for ID: {variable_id} ({variable.descripcion})"
        )

        end_date: datetime = datetime.now()
        start_date: datetime = end_date - timedelta(days=5)

        historical_response: DatosVariableResponse = connector.get_datos_variable(
            variable_id, start_date, end_date, limit=20
        )
        assert isinstance(historical_response, DatosVariableResponse)

        # v4.0 returns DetalleMonetaria instead of DatosVariable
        latest_value: DetalleMonetaria = connector.get_latest_value(variable_id)
        assert latest_value is not None
        assert isinstance(latest_value, DetalleMonetaria)
        assert latest_value.fecha <= end_date.date()

    def test_currency_evolution(self, connector: BCRAConnector) -> None:
        """Test currency evolution over time (Estadisticas Cambiarias)."""
        try:
            evolution: List[CotizacionFecha] = connector.get_evolucion_moneda(
                moneda="USD", limit=10
            )
        except BCRAApiError as e:
            if "La moneda USD no tiene datos para el periodo solicitado" in str(
                e
            ) or "no tiene datos para el periodo solicitado" in str(e):
                pytest.skip("USD evolution data not available for the default period.")
            raise

        assert evolution is not None
        if not evolution:
            connector.logger.warning(
                "USD evolution returned empty list for default period with limit 10."
            )
        else:
            assert len(evolution) > 0 and len(evolution) <= 10
            assert all(isinstance(cf, CotizacionFecha) for cf in evolution)
            first_evolution_point = evolution[0]
            assert first_evolution_point.detalle is not None
            if first_evolution_point.detalle:
                assert any(
                    d.codigo_moneda == "USD" for d in first_evolution_point.detalle
                )

    @pytest.mark.skip(
        reason="Requires specific, valid, and potentially non-existent check data to reliably test."
    )
    def test_check_verification(self, connector: BCRAConnector) -> None:
        """Test check verification workflow (Cheques API)."""
        entities: List[Entidad] = connector.get_entidades()
        if not entities:
            pytest.skip(
                "No financial entities available for testing check verification."
            )

        entity: Entidad = entities[0]
        placeholder_check_number = 123456789

        try:
            is_denunciado: bool = connector.check_denunciado(
                entity.denominacion, placeholder_check_number
            )
            assert isinstance(is_denunciado, bool)
            connector.logger.info(
                f"Check {placeholder_check_number} for {entity.denominacion}: Denounced = {is_denunciado}"
            )
        except ValueError as e:
            pytest.fail(f"ValueError during check_denunciado test: {e}")
        except BCRAApiError as e:
            if "400" in str(e) and "Cuit o formato de cheque inválido" in str(e):
                connector.logger.warning(
                    f"API reported invalid format for entity {entity.codigo_entidad} / check {placeholder_check_number}: {e}"
                )
            else:
                pytest.fail(f"BCRAApiError during check_denunciado test: {e}")

    def test_api_error_for_nonexistent_variable_v3(
        self, connector: BCRAConnector
    ) -> None:
        """Test API error handling for a non-existent variable ID (Monetarias v4.0)."""
        non_existent_id = 9999999
        end_date: datetime = datetime.now()
        start_date: datetime = end_date - timedelta(days=1)

        with pytest.raises(BCRAApiError) as exc_info:
            connector.get_datos_variable(non_existent_id, start_date, end_date)

        error_str = str(exc_info.value).lower()
        assert (
            "404" in error_str
            or "not found" in error_str
            or "400" in error_str
            or "idvariable invalida" in error_str
        ), f"Expected 404/400 or 'not found'/'invalid id' message, got: {exc_info.value}"

    def test_multiple_calls_within_limits(self, connector: BCRAConnector) -> None:
        """Test that a few sequential calls are handled by the rate limiter without errors."""
        call_count = 3
        try:
            for i in range(call_count):
                connector.logger.info(
                    f"Multiple calls test, iteration {i+1}/{call_count}"
                )
                connector.get_principales_variables()
        except BCRAApiError as e:
            pytest.fail(f"BCRAApiError during multiple calls test: {e}")
