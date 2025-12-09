"""Unit tests for principal variables models (Monetarias v4.0)."""

from datetime import date
from typing import Any, Dict, List

import pytest

from bcra_connector.principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
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


class TestDetalleMonetaria:
    """Test suite for DetalleMonetaria model (v4.0)."""

    @pytest.fixture
    def sample_detalle_data(self) -> Dict[str, Any]:
        """Fixture providing sample detalle data."""
        return {"fecha": "2024-03-05", "valor": 100.0}

    def test_detalle_monetaria_from_dict(
        self, sample_detalle_data: Dict[str, Any]
    ) -> None:
        """Test creation of DetalleMonetaria from dictionary."""
        detalle = DetalleMonetaria.from_dict(sample_detalle_data)
        assert detalle.fecha == date(2024, 3, 5)
        assert detalle.valor == 100.0

    def test_detalle_monetaria_to_dict(
        self, sample_detalle_data: Dict[str, Any]
    ) -> None:
        """Test conversion of DetalleMonetaria to dictionary."""
        detalle = DetalleMonetaria.from_dict(sample_detalle_data)
        result = detalle.to_dict()
        assert result == sample_detalle_data

    def test_detalle_monetaria_invalid_date(self) -> None:
        """Test handling of invalid date format."""
        with pytest.raises(
            ValueError, match="Invalid data type or format in DetalleMonetaria data"
        ):
            DetalleMonetaria.from_dict({"fecha": "invalid-date", "valor": 100.0})

    def test_detalle_monetaria_invalid_valor(self) -> None:
        """Test handling of invalid valor type."""
        with pytest.raises(
            ValueError, match="Invalid data type or format in DetalleMonetaria data"
        ):
            DetalleMonetaria.from_dict({"fecha": "2024-01-01", "valor": "not-a-float"})

    def test_detalle_monetaria_missing_fecha(self) -> None:
        """Test handling of missing fecha key."""
        with pytest.raises(ValueError, match="Missing key in DetalleMonetaria data"):
            DetalleMonetaria.from_dict({"valor": 100.0})

    def test_detalle_monetaria_missing_valor(self) -> None:
        """Test handling of missing valor key."""
        with pytest.raises(ValueError, match="Missing key in DetalleMonetaria data"):
            DetalleMonetaria.from_dict({"fecha": "2024-01-01"})


class TestPrincipalesVariables:
    """Test suite for PrincipalesVariables model (v4.0)."""

    @pytest.fixture
    def sample_v4_variable_data(self) -> Dict[str, Any]:
        """Fixture providing sample variable data for v4.0."""
        return {
            "idVariable": 1,
            "descripcion": "Test Variable v4",
            "categoria": "Principales Indicadores",
            "tipoSerie": "Diaria",
            "periodicidad": "D",
            "unidadExpresion": "Millones",
            "moneda": "ARS",
            "primerFechaInformada": "2020-01-01",
            "ultFechaInformada": "2024-03-05",
            "ultValorInformado": 100.0,
        }

    def test_principales_variables_from_dict_v4(
        self, sample_v4_variable_data: Dict[str, Any]
    ) -> None:
        """Test creation of PrincipalesVariables from dictionary (v4.0 format)."""
        variable = PrincipalesVariables.from_dict(sample_v4_variable_data)

        assert variable.idVariable == 1
        assert variable.descripcion == "Test Variable v4"
        assert variable.categoria == "Principales Indicadores"
        assert variable.tipoSerie == "Diaria"
        assert variable.periodicidad == "D"
        assert variable.unidadExpresion == "Millones"
        assert variable.moneda == "ARS"
        assert variable.primerFechaInformada == date(2020, 1, 1)
        assert variable.ultFechaInformada == date(2024, 3, 5)
        assert variable.ultValorInformado == 100.0

    def test_principales_variables_to_dict_v4(
        self, sample_v4_variable_data: Dict[str, Any]
    ) -> None:
        """Test conversion of PrincipalesVariables to dictionary (v4.0 format)."""
        variable = PrincipalesVariables.from_dict(sample_v4_variable_data)
        result = variable.to_dict()

        assert result["idVariable"] == 1
        assert result["descripcion"] == "Test Variable v4"
        assert result["categoria"] == "Principales Indicadores"
        assert result["tipoSerie"] == "Diaria"
        assert result["periodicidad"] == "D"
        assert result["unidadExpresion"] == "Millones"
        assert result["moneda"] == "ARS"
        assert result["primerFechaInformada"] == "2020-01-01"
        assert result["ultFechaInformada"] == "2024-03-05"
        assert result["ultValorInformado"] == 100.0

    def test_principales_variables_minimal_data(self) -> None:
        """Test creation with only required field (idVariable)."""
        minimal_data = {"idVariable": 1}
        variable = PrincipalesVariables.from_dict(minimal_data)
        assert variable.idVariable == 1
        assert variable.descripcion is None
        assert variable.categoria is None

    def test_principales_variables_missing_id(self) -> None:
        """Test handling of missing idVariable field."""
        invalid_data: Dict[str, Any] = {
            "descripcion": "Test Variable",
        }
        with pytest.raises(
            ValueError, match="Missing key in PrincipalesVariables data"
        ):
            PrincipalesVariables.from_dict(invalid_data)

    def test_principales_variables_invalid_date_format(self) -> None:
        """Test handling of invalid date format."""
        invalid_data: Dict[str, Any] = {
            "idVariable": 1,
            "primerFechaInformada": "invalid-date",
        }
        with pytest.raises(
            ValueError, match="Invalid data type or format in PrincipalesVariables data"
        ):
            PrincipalesVariables.from_dict(invalid_data)


class TestDatosVariable:
    """Test suite for DatosVariable model (v4.0)."""

    @pytest.fixture
    def sample_datos_data(self) -> Dict[str, Any]:
        """Fixture providing sample data with detalle array."""
        return {
            "idVariable": 1,
            "detalle": [
                {"fecha": "2024-03-05", "valor": 100.0},
                {"fecha": "2024-03-06", "valor": 105.0},
            ],
        }

    def test_datos_variable_from_dict(self, sample_datos_data: Dict[str, Any]) -> None:
        """Test creation of DatosVariable from dictionary."""
        dato = DatosVariable.from_dict(sample_datos_data)
        assert dato.idVariable == 1
        assert len(dato.detalle) == 2
        assert isinstance(dato.detalle[0], DetalleMonetaria)
        assert dato.detalle[0].fecha == date(2024, 3, 5)
        assert dato.detalle[0].valor == 100.0

    def test_datos_variable_to_dict(self, sample_datos_data: Dict[str, Any]) -> None:
        """Test conversion of DatosVariable to dictionary."""
        dato = DatosVariable.from_dict(sample_datos_data)
        result = dato.to_dict()
        assert result["idVariable"] == 1
        assert len(result["detalle"]) == 2
        assert result["detalle"][0]["fecha"] == "2024-03-05"
        assert result["detalle"][0]["valor"] == 100.0

    def test_datos_variable_empty_detalle(self) -> None:
        """Test DatosVariable with empty detalle list."""
        data = {"idVariable": 1, "detalle": []}
        dato = DatosVariable.from_dict(data)
        assert dato.idVariable == 1
        assert len(dato.detalle) == 0

    def test_datos_variable_post_init_validation(self) -> None:
        """Test __post_init__ validation logic."""
        # Valid case
        DatosVariable(idVariable=1, detalle=[])

        # Invalid idVariable
        with pytest.raises(
            ValueError, match="Variable ID must be a non-negative integer"
        ):
            DatosVariable(idVariable=-1, detalle=[])

        # Invalid detalle type
        with pytest.raises(ValueError, match="Detalle must be a list"):
            DatosVariable(idVariable=1, detalle="not a list")

    def test_datos_variable_equality(self) -> None:
        """Test equality comparison of DatosVariable instances."""
        d1 = DatosVariable(idVariable=1, detalle=[])
        d2 = DatosVariable(idVariable=1, detalle=[])
        d3 = DatosVariable(idVariable=2, detalle=[])

        assert d1 == d2
        assert d1 != d3
        assert d1 != "not a DatosVariable"

    def test_datos_variable_missing_id(self) -> None:
        """Test handling of missing idVariable key."""
        with pytest.raises(ValueError, match="Missing key in DatosVariable data"):
            DatosVariable.from_dict(
                {"detalle": [{"fecha": "2024-01-01", "valor": 10.0}]}
            )


class TestDatosVariableResponse:
    """Test suite for DatosVariableResponse model (v4.0)."""

    @pytest.fixture
    def sample_metadata_dict(self) -> Dict[str, Any]:
        """Sample metadata dictionary."""
        return {"resultset": {"count": 2, "offset": 0, "limit": 10}}

    @pytest.fixture
    def sample_results_list_dict(self) -> List[Dict[str, Any]]:
        """Sample list of results dictionaries (v4.0 format)."""
        return [
            {
                "idVariable": 1,
                "detalle": [
                    {"fecha": "2024-01-01", "valor": 10.0},
                    {"fecha": "2024-01-02", "valor": 12.5},
                ],
            }
        ]

    @pytest.fixture
    def sample_response_data_dict(
        self,
        sample_metadata_dict: Dict[str, Any],
        sample_results_list_dict: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Sample complete response dictionary (v4.0 format)."""
        return {
            "status": 200,
            "metadata": sample_metadata_dict,
            "results": sample_results_list_dict,
        }

    def test_datos_variable_response_from_dict(
        self, sample_response_data_dict: Dict[str, Any]
    ) -> None:
        """Test creation of DatosVariableResponse from dictionary."""
        response = DatosVariableResponse.from_dict(sample_response_data_dict)

        assert response.status == 200
        assert isinstance(response.metadata, Metadata)
        assert response.metadata.resultset.count == 2
        assert len(response.results) == 1
        assert isinstance(response.results[0], DatosVariable)
        assert len(response.results[0].detalle) == 2
        assert response.results[0].detalle[0].valor == 10.0

    def test_datos_variable_response_to_dict(
        self, sample_response_data_dict: Dict[str, Any]
    ) -> None:
        """Test conversion of DatosVariableResponse to dictionary."""
        response = DatosVariableResponse.from_dict(sample_response_data_dict)
        result_dict = response.to_dict()

        # Status
        assert result_dict["status"] == 200
        # Metadata part
        assert (
            result_dict["metadata"]
            == sample_response_data_dict["metadata"]["resultset"]
        )
        # Results part
        assert len(result_dict["results"]) == 1
        assert result_dict["results"][0]["idVariable"] == 1
        assert len(result_dict["results"][0]["detalle"]) == 2

    def test_datos_variable_response_missing_keys(self) -> None:
        """Test from_dict with missing required keys."""
        with pytest.raises(ValueError, match="Missing 'status'"):
            DatosVariableResponse.from_dict({"metadata": {}, "results": []})
        with pytest.raises(ValueError, match="Missing or invalid 'metadata'"):
            DatosVariableResponse.from_dict({"status": 200, "results": []})
        with pytest.raises(ValueError, match="Missing or invalid 'results'"):
            DatosVariableResponse.from_dict(
                {
                    "status": 200,
                    "metadata": {"resultset": {"count": 0, "offset": 0, "limit": 0}},
                }
            )

    def test_datos_variable_response_invalid_types(self) -> None:
        """Test from_dict with invalid types for fields."""
        with pytest.raises(ValueError, match="Missing or invalid 'metadata'"):
            DatosVariableResponse.from_dict(
                {"status": 200, "metadata": "not a dict", "results": []}
            )
        with pytest.raises(ValueError, match="Missing or invalid 'results'"):
            DatosVariableResponse.from_dict(
                {
                    "status": 200,
                    "metadata": {"resultset": {"count": 0, "offset": 0, "limit": 0}},
                    "results": "not a list",
                }
            )

    def test_datos_variable_response_parsing_error_in_children(self) -> None:
        """Test error handling when child models fail to parse."""
        invalid_results_data = [
            {
                "idVariable": "invalid",  # Should be int
                "detalle": [{"fecha": "2024-01-01", "valor": 10.0}],
            }
        ]
        data = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 10}},
            "results": invalid_results_data,
        }
        with pytest.raises(
            ValueError, match="Error parsing components of DatosVariableResponse"
        ):
            DatosVariableResponse.from_dict(data)
