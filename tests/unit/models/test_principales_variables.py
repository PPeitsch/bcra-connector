"""Unit tests for principal variables models."""

from datetime import date
from typing import Any, Dict

import pytest

from bcra_connector.principales_variables import DatosVariable, PrincipalesVariables


class TestPrincipalesVariables:
    """Test suite for PrincipalesVariables model."""

    @pytest.fixture
    def sample_variable_data(self) -> Dict[str, Any]:
        """Fixture providing sample variable data."""
        return {
            "idVariable": 1,
            "cdSerie": 246,
            "descripcion": "Test Variable",
            "fecha": "2024-03-05",
            "valor": 100.0,
        }

    def test_principales_variables_from_dict(
        self, sample_variable_data: Dict[str, Any]
    ) -> None:
        """Test creation of PrincipalesVariables from dictionary."""
        variable: PrincipalesVariables = PrincipalesVariables.from_dict(
            sample_variable_data
        )

        assert variable.idVariable == 1
        assert variable.cdSerie == 246
        assert variable.descripcion == "Test Variable"
        assert variable.fecha == date(2024, 3, 5)
        assert variable.valor == 100.0

    def test_principales_variables_invalid_date(self) -> None:
        """Test handling of invalid date format."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "cdSerie": 246,
            "descripcion": "Test Variable",
            "fecha": "invalid-date",
            "valor": 100.0,
        }
        with pytest.raises(ValueError):
            PrincipalesVariables.from_dict(invalid_data)

    def test_principales_variables_missing_fields(self) -> None:
        """Test handling of missing required fields."""
        incomplete_data: Dict[str, Any] = {
            "idVariable": 1,
            "descripcion": "Test Variable",
        }
        with pytest.raises(KeyError):
            PrincipalesVariables.from_dict(incomplete_data)

    def test_principales_variables_invalid_valor(self) -> None:
        """Test handling of invalid valor type."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "cdSerie": 246,
            "descripcion": "Test Variable",
            "fecha": "2024-03-05",
            "valor": "not-a-number",
        }
        with pytest.raises(ValueError):
            PrincipalesVariables.from_dict(invalid_data)

    def test_principales_variables_to_dict(
        self, sample_variable_data: Dict[str, Any]
    ) -> None:
        """Test conversion of PrincipalesVariables to dictionary."""
        variable = PrincipalesVariables.from_dict(sample_variable_data)
        result = variable.to_dict()

        assert result["idVariable"] == 1
        assert result["cdSerie"] == 246
        assert result["descripcion"] == "Test Variable"
        assert result["fecha"] == "2024-03-05"
        assert result["valor"] == 100.0


class TestDatosVariable:
    """Test suite for DatosVariable model."""

    @pytest.fixture
    def sample_datos_data(self) -> Dict[str, Any]:
        """Fixture providing sample data point."""
        return {"idVariable": 1, "fecha": "2024-03-05", "valor": 100.0}

    def test_datos_variable_from_dict(self, sample_datos_data: Dict[str, Any]) -> None:
        """Test creation of DatosVariable from dictionary."""
        dato: DatosVariable = DatosVariable.from_dict(sample_datos_data)

        assert dato.idVariable == 1
        assert dato.fecha == date(2024, 3, 5)
        assert dato.valor == 100.0

    def test_datos_variable_invalid_date(self) -> None:
        """Test handling of invalid date format."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "fecha": "invalid-date",
            "valor": 100.0,
        }
        with pytest.raises(ValueError):
            DatosVariable.from_dict(invalid_data)

    def test_datos_variable_missing_fields(self) -> None:
        """Test handling of missing required fields."""
        incomplete_data: Dict[str, Any] = {"idVariable": 1, "fecha": "2024-03-05"}
        with pytest.raises(KeyError):
            DatosVariable.from_dict(incomplete_data)

    def test_datos_variable_invalid_valor(self) -> None:
        """Test handling of invalid valor type."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "fecha": "2024-03-05",
            "valor": "not-a-number",
        }
        with pytest.raises(ValueError):
            DatosVariable.from_dict(invalid_data)

    def test_datos_variable_negative_id(self) -> None:
        """Test validation of negative variable ID."""
        invalid_data: Dict[str, Any] = {
            "idVariable": -1,
            "fecha": "2024-03-05",
            "valor": 100.0,
        }
        with pytest.raises(ValueError):
            DatosVariable.from_dict(invalid_data)

    def test_datos_variable_comparison(self) -> None:
        """Test equality comparison between DatosVariable instances."""
        dato1: DatosVariable = DatosVariable(
            idVariable=1, fecha=date(2024, 3, 5), valor=100.0
        )
        dato2: DatosVariable = DatosVariable(
            idVariable=1, fecha=date(2024, 3, 6), valor=101.0
        )

        assert dato1 != dato2
        assert dato1 == dato1  # Same instance
        assert dato1 is not dato2

    def test_datos_variable_same_date_comparison(self) -> None:
        """Test comparison of DatosVariable with same date."""
        dato1: DatosVariable = DatosVariable(
            idVariable=1, fecha=date(2024, 3, 5), valor=100.0
        )
        dato2: DatosVariable = DatosVariable(
            idVariable=1, fecha=date(2024, 3, 5), valor=101.0
        )

        assert dato1 == dato2  # Same date should be considered equal

    def test_datos_variable_to_dict(self, sample_datos_data: Dict[str, Any]) -> None:
        """Test conversion of DatosVariable to dictionary."""
        dato = DatosVariable.from_dict(sample_datos_data)
        result = dato.to_dict()

        assert result["idVariable"] == 1
        assert result["fecha"] == "2024-03-05"
        assert result["valor"] == 100.0
