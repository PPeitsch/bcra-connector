"""Unit tests for principal variables models (Monetarias v3.0)."""

from datetime import date
from typing import Any, Dict, List

import pytest

from bcra_connector.principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    Metadata,
    PrincipalesVariables,
    Resultset,
)


class TestResultset:
    """Test suite for Resultset model."""

    def test_resultset_creation_and_to_dict(self) -> None:
        """Test Resultset creation from_dict and conversion to_dict."""
        data = {"count": 100, "offset": 0, "limit": 50}
        resultset = Resultset.from_dict(data)
        assert resultset.count == 100
        assert resultset.offset == 0
        assert resultset.limit == 50
        assert resultset.to_dict() == data

    def test_resultset_invalid_types(self) -> None:
        """Test Resultset creation with invalid data types."""
        with pytest.raises(ValueError, match="Invalid types for Resultset fields"):
            Resultset.from_dict({"count": "100", "offset": 0, "limit": 50})
        with pytest.raises(ValueError, match="Invalid types for Resultset fields"):
            Resultset.from_dict({"count": 100, "offset": None, "limit": 50})


class TestMetadata:
    """Test suite for Metadata model."""

    def test_metadata_creation(self) -> None:
        """Test Metadata creation from_dict."""
        data = {"resultset": {"count": 100, "offset": 0, "limit": 50}}
        metadata = Metadata.from_dict(data)
        assert isinstance(metadata.resultset, Resultset)
        assert metadata.resultset.count == 100

    def test_metadata_missing_resultset(self) -> None:
        """Test Metadata creation with missing resultset key."""
        with pytest.raises(
            ValueError, match="Missing or invalid 'resultset' in Metadata"
        ):
            Metadata.from_dict({})

    def test_metadata_invalid_resultset_type(self) -> None:
        """Test Metadata creation with invalid resultset type."""
        with pytest.raises(
            ValueError, match="Missing or invalid 'resultset' in Metadata"
        ):
            Metadata.from_dict({"resultset": "not a dict"})


class TestPrincipalesVariables:
    """Test suite for PrincipalesVariables model (v3.0)."""

    @pytest.fixture
    def sample_v3_variable_data(self) -> Dict[str, Any]:
        """Fixture providing sample variable data for v3.0."""
        return {
            "idVariable": 1,
            "descripcion": "Test Variable v3",
            "fecha": "2024-03-05",
            "valor": 100.0,
            "categoria": "Principales Indicadores",
        }

    def test_principales_variables_from_dict_v3(
        self, sample_v3_variable_data: Dict[str, Any]
    ) -> None:
        """Test creation of PrincipalesVariables from dictionary (v3.0 format)."""
        variable: PrincipalesVariables = PrincipalesVariables.from_dict(
            sample_v3_variable_data
        )

        assert variable.idVariable == 1
        assert variable.descripcion == "Test Variable v3"
        assert variable.fecha == date(2024, 3, 5)
        assert variable.valor == 100.0
        assert variable.categoria == "Principales Indicadores"

    def test_principales_variables_to_dict_v3(
        self, sample_v3_variable_data: Dict[str, Any]
    ) -> None:
        """Test conversion of PrincipalesVariables to dictionary (v3.0 format)."""
        variable = PrincipalesVariables.from_dict(sample_v3_variable_data)
        result = variable.to_dict()

        assert result["idVariable"] == 1
        assert "cdSerie" not in result  # Ensure cdSerie is not in dict
        assert result["descripcion"] == "Test Variable v3"
        assert result["fecha"] == "2024-03-05"
        assert result["valor"] == 100.0
        assert result["categoria"] == "Principales Indicadores"

    def test_principales_variables_missing_categoria(self) -> None:
        """Test handling of missing 'categoria' field (v3.0)."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "descripcion": "Test Variable",
            "fecha": "2024-03-05",
            "valor": 100.0,
            # "categoria" is missing
        }
        with pytest.raises(
            ValueError, match="Missing key in PrincipalesVariables data: 'categoria'"
        ):
            PrincipalesVariables.from_dict(invalid_data)

    def test_principales_variables_invalid_date_format(self) -> None:
        """Test handling of invalid date format."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "descripcion": "Test",
            "fecha": "invalid-date",
            "valor": 100.0,
            "categoria": "TestCat",
        }
        with pytest.raises(
            ValueError, match="Invalid data type or format in PrincipalesVariables data"
        ):
            PrincipalesVariables.from_dict(invalid_data)

    def test_principales_variables_invalid_value_type(self) -> None:
        """Test handling of invalid valor type."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "descripcion": "Test",
            "fecha": "2024-01-01",
            "valor": "not-a-float",
            "categoria": "TestCat",
        }
        with pytest.raises(
            ValueError, match="Invalid data type or format in PrincipalesVariables data"
        ):
            PrincipalesVariables.from_dict(invalid_data)


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

    def test_datos_variable_to_dict(self, sample_datos_data: Dict[str, Any]) -> None:
        """Test conversion of DatosVariable to dictionary."""
        dato = DatosVariable.from_dict(sample_datos_data)
        result = dato.to_dict()
        assert result == sample_datos_data  # Assuming valor is float in sample

    def test_datos_variable_post_init_validation(self) -> None:
        """Test __post_init__ validation logic."""
        # Valid cases
        DatosVariable(idVariable=1, fecha=date(2024, 1, 1), valor=10.0)
        DatosVariable(
            idVariable=0, fecha=date(2024, 1, 1), valor=0
        )  # int valor converted

        # Invalid idVariable
        with pytest.raises(
            ValueError, match="Variable ID must be a non-negative integer"
        ):
            DatosVariable(idVariable=-1, fecha=date(2024, 1, 1), valor=10.0)
        with pytest.raises(
            ValueError, match="Variable ID must be a non-negative integer"
        ):
            DatosVariable(idVariable="1", fecha=date(2024, 1, 1), valor=10.0)

        # Invalid fecha
        with pytest.raises(ValueError, match="Fecha must be a date object"):
            DatosVariable(idVariable=1, fecha="2024-01-01", valor=10.0)

        # Invalid valor type (after from_dict would attempt float conversion)
        # This tests direct instantiation with a bad type that __post_init__ should catch.
        # The __post_init__ you used: if not isinstance(self.valor, (int, float)):
        with pytest.raises(ValueError, match="Valor must be a number, got str"):
            DatosVariable(idVariable=1, fecha=date(2024, 1, 1), valor="abc")

    def test_datos_variable_from_dict_invalid_data(self) -> None:
        """Test from_dict with various invalid input data."""
        with pytest.raises(
            ValueError, match="Missing key in DatosVariable data: 'idVariable'"
        ):
            DatosVariable.from_dict({"fecha": "2024-01-01", "valor": 10.0})
        with pytest.raises(
            ValueError, match="Invalid data type or format in DatosVariable data"
        ):
            DatosVariable.from_dict(
                {"idVariable": 1, "fecha": "invalid", "valor": 10.0}
            )
        with pytest.raises(
            ValueError, match="Invalid data type or format in DatosVariable data"
        ):
            DatosVariable.from_dict(
                {"idVariable": 1, "fecha": "2024-01-01", "valor": "abc"}
            )

    def test_datos_variable_equality(self) -> None:
        """Test equality comparison of DatosVariable instances."""
        d1 = DatosVariable(idVariable=1, fecha=date(2024, 1, 1), valor=10.0)
        d2 = DatosVariable(
            idVariable=1, fecha=date(2024, 1, 1), valor=20.0
        )  # Same ID and date
        d3 = DatosVariable(
            idVariable=1, fecha=date(2024, 1, 2), valor=10.0
        )  # Different date
        d4 = DatosVariable(
            idVariable=2, fecha=date(2024, 1, 1), valor=10.0
        )  # Different ID

        assert d1 == d2
        assert d1 != d3
        assert d1 != d4
        assert d1 != "not a DatosVariable"


class TestDatosVariableResponse:
    """Test suite for DatosVariableResponse model."""

    @pytest.fixture
    def sample_metadata_dict(self) -> Dict[str, Any]:
        """Sample metadata dictionary."""
        return {"resultset": {"count": 2, "offset": 0, "limit": 10}}

    @pytest.fixture
    def sample_results_list_dict(self) -> List[Dict[str, Any]]:
        """Sample list of results dictionaries."""
        return [
            {"idVariable": 1, "fecha": "2024-01-01", "valor": 10.0},
            {"idVariable": 1, "fecha": "2024-01-02", "valor": 12.5},
        ]

    @pytest.fixture
    def sample_response_data_dict(
        self,
        sample_metadata_dict: Dict[str, Any],
        sample_results_list_dict: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Sample complete response dictionary."""
        return {"metadata": sample_metadata_dict, "results": sample_results_list_dict}

    def test_datos_variable_response_from_dict(
        self, sample_response_data_dict: Dict[str, Any]
    ) -> None:
        """Test creation of DatosVariableResponse from dictionary."""
        response = DatosVariableResponse.from_dict(sample_response_data_dict)

        assert isinstance(response.metadata, Metadata)
        assert response.metadata.resultset.count == 2
        assert len(response.results) == 2
        assert isinstance(response.results[0], DatosVariable)
        assert response.results[0].valor == 10.0

    def test_datos_variable_response_to_dict(
        self, sample_response_data_dict: Dict[str, Any]
    ) -> None:
        """Test conversion of DatosVariableResponse to dictionary."""
        response = DatosVariableResponse.from_dict(sample_response_data_dict)
        result_dict = response.to_dict()

        # Metadata part
        assert (
            result_dict["metadata"]
            == sample_response_data_dict["metadata"]["resultset"]
        )
        # Results part
        assert len(result_dict["results"]) == len(sample_response_data_dict["results"])
        for original, converted in zip(
            sample_response_data_dict["results"], result_dict["results"]
        ):
            assert converted["idVariable"] == original["idVariable"]
            assert converted["fecha"] == original["fecha"]
            assert converted["valor"] == original["valor"]

    def test_datos_variable_response_missing_keys(self) -> None:
        """Test from_dict with missing 'metadata' or 'results' keys."""
        with pytest.raises(ValueError, match="Missing or invalid 'metadata'"):
            DatosVariableResponse.from_dict({"results": []})
        with pytest.raises(ValueError, match="Missing or invalid 'results'"):
            DatosVariableResponse.from_dict(
                {"metadata": {"resultset": {"count": 0, "offset": 0, "limit": 0}}}
            )

    def test_datos_variable_response_invalid_types(self) -> None:
        """Test from_dict with invalid types for 'metadata' or 'results'."""
        with pytest.raises(ValueError, match="Missing or invalid 'metadata'"):
            DatosVariableResponse.from_dict({"metadata": "not a dict", "results": []})
        with pytest.raises(ValueError, match="Missing or invalid 'results'"):
            DatosVariableResponse.from_dict(
                {"metadata": {"resultset": {}}, "results": "not a list"}
            )

    def test_datos_variable_response_parsing_error_in_children(self) -> None:
        """Test error handling when child models fail to parse."""
        invalid_results_data = [
            {"idVariable": 1, "fecha": "2024-01-01", "valor": 10.0},
            {
                "idVariable": "invalid",
                "fecha": "2024-01-02",
                "valor": 12.5,
            },  # bad idVariable
        ]
        data = {
            "metadata": {"resultset": {"count": 2, "offset": 0, "limit": 10}},
            "results": invalid_results_data,
        }
        with pytest.raises(
            ValueError, match="Error parsing components of DatosVariableResponse"
        ):
            DatosVariableResponse.from_dict(data)
