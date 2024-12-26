"""Unit tests for currency exchange statistics models."""

from datetime import date
from typing import Any, Dict

import pytest

from bcra_connector.estadisticas_cambiarias import (
    CotizacionDetalle,
    CotizacionesResponse,
    CotizacionFecha,
    CotizacionResponse,
    Divisa,
    DivisaResponse,
    ErrorResponse,
    Metadata,
    Resultset,
)


class TestDivisa:
    """Test suite for Divisa model."""

    @pytest.fixture
    def sample_divisa_data(self) -> Dict[str, Any]:
        """Fixture providing sample currency data."""
        return {"codigo": "USD", "denominacion": "DOLAR ESTADOUNIDENSE"}

    def test_divisa_from_dict(self, sample_divisa_data: Dict[str, Any]) -> None:
        """Test creation of Divisa from dictionary."""
        divisa: Divisa = Divisa.from_dict(sample_divisa_data)

        assert divisa.codigo == "USD"
        assert divisa.denominacion == "DOLAR ESTADOUNIDENSE"

    def test_divisa_missing_fields(self) -> None:
        """Test handling of missing required fields."""
        incomplete_data: Dict[str, Any] = {"codigo": "USD"}
        with pytest.raises(KeyError):
            Divisa.from_dict(incomplete_data)

    def test_divisa_invalid_code(self) -> None:
        """Test validation of currency code."""
        invalid_data: Dict[str, Any] = {
            "codigo": "",  # Empty code
            "denominacion": "TEST",
        }
        with pytest.raises(ValueError):
            Divisa.from_dict(invalid_data)

    def test_divisa_validation(self) -> None:
        """Test Divisa validation with invalid data."""
        # Test empty code
        with pytest.raises(ValueError, match="Currency code cannot be empty"):
            Divisa(codigo="   ", denominacion="US Dollar")

        # Test empty denomination
        with pytest.raises(ValueError, match="Currency name cannot be empty"):
            Divisa(codigo="USD", denominacion="  ")

    def test_divisa_empty_denomination(self) -> None:
        """Test validation of empty denomination."""
        # Test empty denomination
        with pytest.raises(ValueError, match="Currency name cannot be empty"):
            Divisa(codigo="USD", denominacion="   ")


class TestCotizacionDetalle:
    """Test suite for CotizacionDetalle model."""

    @pytest.fixture
    def sample_cotizacion_detalle_data(self) -> Dict[str, Any]:
        """Fixture providing sample quotation detail data."""
        return {
            "codigoMoneda": "USD",
            "descripcion": "DOLAR ESTADOUNIDENSE",
            "tipoPase": 1.0,
            "tipoCotizacion": 43.6862,
        }

    def test_cotizacion_detalle_from_dict(
        self, sample_cotizacion_detalle_data: Dict[str, Any]
    ) -> None:
        """Test creation of CotizacionDetalle from dictionary."""
        detalle: CotizacionDetalle = CotizacionDetalle.from_dict(
            sample_cotizacion_detalle_data
        )

        assert detalle.codigo_moneda == "USD"
        assert detalle.descripcion == "DOLAR ESTADOUNIDENSE"
        assert detalle.tipo_pase == 1.0
        assert detalle.tipo_cotizacion == 43.6862

    def test_cotizacion_detalle_invalid_values(self) -> None:
        """Test handling of invalid numeric values."""
        invalid_data: Dict[str, Any] = {
            "codigoMoneda": "USD",
            "descripcion": "TEST",
            "tipoPase": "not-a-number",
            "tipoCotizacion": 43.6862,
        }
        with pytest.raises(ValueError):
            CotizacionDetalle.from_dict(invalid_data)


class TestCotizacionFecha:
    """Test suite for CotizacionFecha model."""

    @pytest.fixture
    def sample_cotizacion_fecha_data(self) -> Dict[str, Any]:
        """Fixture providing sample dated quotation data."""
        return {
            "fecha": "2024-03-05",
            "detalle": [
                {
                    "codigoMoneda": "USD",
                    "descripcion": "DOLAR ESTADOUNIDENSE",
                    "tipoPase": 1.0,
                    "tipoCotizacion": 43.6862,
                }
            ],
        }

    def test_cotizacion_fecha_from_dict(
        self, sample_cotizacion_fecha_data: Dict[str, Any]
    ) -> None:
        """Test creation of CotizacionFecha from dictionary."""
        cotizacion: CotizacionFecha = CotizacionFecha.from_dict(
            sample_cotizacion_fecha_data
        )

        assert cotizacion.fecha == date(2024, 3, 5)
        assert len(cotizacion.detalle) == 1
        assert isinstance(cotizacion.detalle[0], CotizacionDetalle)
        assert cotizacion.detalle[0].codigo_moneda == "USD"

    def test_cotizacion_fecha_with_null_date(self) -> None:
        """Test handling of null date."""
        data: Dict[str, Any] = {"fecha": None, "detalle": []}
        cotizacion: CotizacionFecha = CotizacionFecha.from_dict(data)

        assert cotizacion.fecha is None
        assert len(cotizacion.detalle) == 0

    def test_cotizacion_fecha_to_dict_with_null_date(self) -> None:
        """Test to_dict() method with null date."""
        data: Dict[str, Any] = {"fecha": None, "detalle": []}
        cotizacion = CotizacionFecha.from_dict(data)
        result = cotizacion.to_dict()

        assert result["fecha"] is None
        assert isinstance(result["detalle"], list)
        assert len(result["detalle"]) == 0

    def test_none_fecha_handling(self) -> None:
        """Test handling of None fecha in CotizacionFecha."""
        data: Dict[str, Any] = {"fecha": None, "detalle": []}
        cotizacion = CotizacionFecha.from_dict(data)
        assert cotizacion.fecha is None
        assert len(cotizacion.detalle) == 0

        # Test to_dict with None fecha
        result = cotizacion.to_dict()
        assert result["fecha"] is None
        assert result["detalle"] == []


class TestResponseModels:
    """Test suite for response models."""

    @pytest.fixture
    def sample_cotizacion_fecha_data(self) -> Dict[str, Any]:
        """Fixture providing sample dated quotation data."""
        return {
            "fecha": "2024-03-05",
            "detalle": [
                {
                    "codigoMoneda": "USD",
                    "descripcion": "DOLAR ESTADOUNIDENSE",
                    "tipoPase": 1.0,
                    "tipoCotizacion": 43.6862,
                }
            ],
        }

    def test_resultset(self) -> None:
        """Test Resultset model."""
        data: Dict[str, Any] = {"count": 1, "offset": 0, "limit": 1000}
        resultset: Resultset = Resultset.from_dict(data)

        assert resultset.count == 1
        assert resultset.offset == 0
        assert resultset.limit == 1000

    def test_metadata(self) -> None:
        """Test Metadata model."""
        data: Dict[str, Any] = {"resultset": {"count": 1, "offset": 0, "limit": 1000}}
        metadata: Metadata = Metadata.from_dict(data)

        assert metadata.resultset.count == 1
        assert metadata.resultset.offset == 0
        assert metadata.resultset.limit == 1000

    def test_divisa_response(self) -> None:
        """Test DivisaResponse model."""
        data: Dict[str, Any] = {
            "status": 200,
            "results": [
                {"codigo": "USD", "denominacion": "DOLAR ESTADOUNIDENSE"},
                {"codigo": "EUR", "denominacion": "EURO"},
            ],
        }
        response: DivisaResponse = DivisaResponse.from_dict(data)

        assert response.status == 200
        assert len(response.results) == 2
        assert isinstance(response.results[0], Divisa)
        assert response.results[0].codigo == "USD"
        assert response.results[1].denominacion == "EURO"

    def test_cotizacion_response(
        self, sample_cotizacion_fecha_data: Dict[str, Any]
    ) -> None:
        """Test CotizacionResponse model."""
        data: Dict[str, Any] = {"status": 200, "results": sample_cotizacion_fecha_data}
        response: CotizacionResponse = CotizacionResponse.from_dict(data)

        assert response.status == 200
        assert isinstance(response.results, CotizacionFecha)
        assert response.results.fecha == date(2024, 3, 5)

    def test_cotizaciones_response(
        self, sample_cotizacion_fecha_data: Dict[str, Any]
    ) -> None:
        """Test CotizacionesResponse model."""
        data: Dict[str, Any] = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 1000}},
            "results": [sample_cotizacion_fecha_data],
        }
        response: CotizacionesResponse = CotizacionesResponse.from_dict(data)

        assert response.status == 200
        assert response.metadata.resultset.count == 1
        assert len(response.results) == 1
        assert isinstance(response.results[0], CotizacionFecha)

    def test_error_response(self) -> None:
        """Test ErrorResponse model."""
        data: Dict[str, Any] = {
            "status": 400,
            "errorMessages": ["La fecha desde no puede ser mayor a la fecha hasta."],
        }
        response: ErrorResponse = ErrorResponse.from_dict(data)

        assert response.status == 400
        assert len(response.error_messages) == 1
        assert "fecha desde" in response.error_messages[0]
