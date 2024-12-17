"""Unit tests for check-related models."""

from datetime import date
from typing import Dict, Any

import pytest
from bcra_connector.cheques import (
    Cheque,
    ChequeDetalle,
    ChequeResponse,
    Entidad,
    EntidadResponse,
    ErrorResponse
)


class TestEntidad:
    """Test suite for Entidad model."""

    def test_entidad_creation(self) -> None:
        """Test creation of Entidad instances."""
        data: Dict[str, Any] = {
            "codigoEntidad": 11,
            "denominacion": "BANCO DE LA NACION ARGENTINA"
        }
        entidad: Entidad = Entidad.from_dict(data)

        assert entidad.codigo_entidad == 11
        assert entidad.denominacion == "BANCO DE LA NACION ARGENTINA"

    def test_entidad_to_dict(self) -> None:
        """Test conversion of Entidad to dictionary."""
        entidad: Entidad = Entidad(
            codigo_entidad=14,
            denominacion="BANCO DE LA PROVINCIA DE BUENOS AIRES"
        )
        data: Dict[str, Any] = entidad.to_dict()

        assert data["codigoEntidad"] == 14
        assert data["denominacion"] == "BANCO DE LA PROVINCIA DE BUENOS AIRES"

    def test_entidad_equality(self) -> None:
        """Test equality comparison of Entidad instances."""
        entidad1: Entidad = Entidad(codigo_entidad=11, denominacion="BANCO TEST")
        entidad2: Entidad = Entidad(codigo_entidad=11, denominacion="BANCO TEST")
        entidad3: Entidad = Entidad(codigo_entidad=12, denominacion="BANCO TEST")

        assert entidad1 == entidad2
        assert entidad1 != entidad3
        assert entidad1 != "not an entidad"


class TestChequeDetalle:
    """Test suite for ChequeDetalle model."""

    def test_cheque_detalle_creation(self) -> None:
        """Test creation of ChequeDetalle instances."""
        data: Dict[str, Any] = {
            "sucursal": 524,
            "numeroCuenta": 5240055962,
            "causal": "Denuncia por robo"
        }
        detalle: ChequeDetalle = ChequeDetalle.from_dict(data)

        assert detalle.sucursal == 524
        assert detalle.numero_cuenta == 5240055962
        assert detalle.causal == "Denuncia por robo"

    def test_cheque_detalle_to_dict(self) -> None:
        """Test conversion of ChequeDetalle to dictionary."""
        detalle: ChequeDetalle = ChequeDetalle(
            sucursal=524,
            numero_cuenta=5240055962,
            causal="Denuncia por robo"
        )
        data: Dict[str, Any] = detalle.to_dict()

        assert data["sucursal"] == 524
        assert data["numeroCuenta"] == 5240055962
        assert data["causal"] == "Denuncia por robo"


class TestCheque:
    """Test suite for Cheque model."""

    @pytest.fixture
    def sample_cheque_data(self) -> Dict[str, Any]:
        """Fixture providing sample check data."""
        return {
            "numeroCheque": 20377516,
            "denunciado": True,
            "fechaProcesamiento": "2024-03-05",
            "denominacionEntidad": "BANCO DE LA NACION ARGENTINA",
            "detalles": [
                {
                    "sucursal": 524,
                    "numeroCuenta": 5240055962,
                    "causal": "Denuncia por robo"
                }
            ]
        }

    def test_cheque_creation(self, sample_cheque_data: Dict[str, Any]) -> None:
        """Test creation of Cheque instances."""
        cheque: Cheque = Cheque.from_dict(sample_cheque_data)

        assert cheque.numero_cheque == 20377516
        assert cheque.denunciado is True
        assert cheque.fecha_procesamiento == date(2024, 3, 5)
        assert cheque.denominacion_entidad == "BANCO DE LA NACION ARGENTINA"
        assert len(cheque.detalles) == 1
        assert isinstance(cheque.detalles[0], ChequeDetalle)

    def test_cheque_to_dict(self, sample_cheque_data: Dict[str, Any]) -> None:
        """Test conversion of Cheque to dictionary."""
        cheque: Cheque = Cheque.from_dict(sample_cheque_data)
        data: Dict[str, Any] = cheque.to_dict()

        assert data["numeroCheque"] == 20377516
        assert data["denunciado"] is True
        assert data["fechaProcesamiento"] == "2024-03-05"
        assert len(data["detalles"]) == 1

    def test_cheque_with_no_detalles(self) -> None:
        """Test Cheque creation with no details."""
        data: Dict[str, Any] = {
            "numeroCheque": 20377516,
            "denunciado": False,
            "fechaProcesamiento": "2024-03-05",
            "denominacionEntidad": "BANCO TEST",
            "detalles": []
        }
        cheque: Cheque = Cheque.from_dict(data)

        assert len(cheque.detalles) == 0


class TestResponses:
    """Test suite for API response models."""

    def test_entidad_response(self) -> None:
        """Test EntidadResponse model."""
        data: Dict[str, Any] = {
            "status": 200,
            "results": [
                {
                    "codigoEntidad": 11,
                    "denominacion": "BANCO DE LA NACION ARGENTINA"
                }
            ]
        }
        response: EntidadResponse = EntidadResponse.from_dict(data)

        assert response.status == 200
        assert len(response.results) == 1
        assert isinstance(response.results[0], Entidad)

    def test_cheque_response(self, sample_cheque_data: Dict[str, Any]) -> None:
        """Test ChequeResponse model."""
        data: Dict[str, Any] = {
            "status": 200,
            "results": sample_cheque_data
        }
        response: ChequeResponse = ChequeResponse.from_dict(data)

        assert response.status == 200
        assert isinstance(response.results, Cheque)

    def test_error_response(self) -> None:
        """Test ErrorResponse model."""
        data: Dict[str, Any] = {
            "status": 400,
            "errorMessages": ["Invalid check number"]
        }
        response: ErrorResponse = ErrorResponse.from_dict(data)

        assert response.status == 400
        assert len(response.error_messages) == 1
        assert response.error_messages[0] == "Invalid check number"

    def test_error_response_multiple_messages(self) -> None:
        """Test ErrorResponse with multiple error messages."""
        data: Dict[str, Any] = {
            "status": 400,
            "errorMessages": [
                "Invalid check number",
                "Invalid entity code"
            ]
        }
        response: ErrorResponse = ErrorResponse.from_dict(data)

        assert len(response.error_messages) == 2


class TestValidation:
    """Test suite for model validation."""

    def test_invalid_date_format(self) -> None:
        """Test handling of invalid date format."""
        with pytest.raises(ValueError):
            Cheque(
                numero_cheque=1,
                denunciado=True,
                fecha_procesamiento="invalid-date",
                denominacion_entidad="TEST",
                detalles=[]
            )

    def test_negative_check_number(self) -> None:
        """Test validation of negative check numbers."""
        with pytest.raises(ValueError):
            Cheque(
                numero_cheque=-1,
                denunciado=True,
                fecha_procesamiento=date.today(),
                denominacion_entidad="TEST",
                detalles=[]
            )

    def test_empty_entity_name(self) -> None:
        """Test validation of empty entity names."""
        with pytest.raises(ValueError):
            Entidad(codigo_entidad=1, denominacion="")
