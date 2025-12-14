"""
Unit tests for to_dataframe() methods across all data models.
Tests DataFrame conversion functionality for pandas integration.
"""

from unittest.mock import patch

import pytest

# Test data fixtures
PRINCIPALES_VARIABLES_DATA = {
    "idVariable": 1,
    "descripcion": "Test Variable",
    "categoria": "Test Category",
    "tipoSerie": "Daily",
    "periodicidad": "Diaria",
    "unidadExpresion": "Unidades",
    "moneda": "ARS",
    "primerFechaInformada": "2020-01-01",
    "ultFechaInformada": "2024-01-01",
    "ultValorInformado": 100.5,
}

DETALLE_MONETARIA_DATA = {"fecha": "2024-01-15", "valor": 123.45}

DATOS_VARIABLE_DATA = {
    "idVariable": 1,
    "detalle": [
        {"fecha": "2024-01-01", "valor": 100.0},
        {"fecha": "2024-01-02", "valor": 101.5},
        {"fecha": "2024-01-03", "valor": 102.0},
    ],
}

ENTIDAD_DATA = {"codigoEntidad": 123, "denominacion": "Banco Test"}

CHEQUE_DATA = {
    "numeroCheque": 12345,
    "denunciado": True,
    "fechaProcesamiento": "2024-01-15",
    "denominacionEntidad": "Banco Test",
    "detalles": [
        {"sucursal": 1, "numeroCuenta": 1001, "causal": "Robo"},
        {"sucursal": 2, "numeroCuenta": 1002, "causal": "Extraviado"},
    ],
}

COTIZACION_FECHA_DATA = {
    "fecha": "2024-01-15",
    "detalle": [
        {
            "codigoMoneda": "USD",
            "descripcion": "Dolar",
            "tipoPase": 800.0,
            "tipoCotizacion": 850.0,
        },
        {
            "codigoMoneda": "EUR",
            "descripcion": "Euro",
            "tipoPase": 900.0,
            "tipoCotizacion": 950.0,
        },
    ],
}


class TestPrincipalesVariablesToDataframe:
    """Tests for PrincipalesVariables.to_dataframe() method."""

    def test_to_dataframe_returns_dataframe(self) -> None:
        """Test that to_dataframe returns a pandas DataFrame."""
        import pandas as pd

        from bcra_connector.principales_variables import PrincipalesVariables

        var = PrincipalesVariables.from_dict(PRINCIPALES_VARIABLES_DATA)
        df = var.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["idVariable"] == 1
        assert df.iloc[0]["descripcion"] == "Test Variable"

    def test_to_dataframe_without_pandas_raises_import_error(self) -> None:
        """Test that ImportError is raised when pandas is not installed."""
        from bcra_connector.principales_variables import PrincipalesVariables

        var = PrincipalesVariables.from_dict(PRINCIPALES_VARIABLES_DATA)

        with patch.dict("sys.modules", {"pandas": None}):
            with pytest.raises(ImportError, match="pandas is required"):
                var.to_dataframe()


class TestDetalleMonetariaToDataframe:
    """Tests for DetalleMonetaria.to_dataframe() method."""

    def test_to_dataframe_returns_dataframe(self) -> None:
        """Test that to_dataframe returns a pandas DataFrame."""
        import pandas as pd

        from bcra_connector.principales_variables import DetalleMonetaria

        detalle = DetalleMonetaria.from_dict(DETALLE_MONETARIA_DATA)
        df = detalle.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["valor"] == 123.45


class TestDatosVariableToDataframe:
    """Tests for DatosVariable.to_dataframe() method."""

    def test_to_dataframe_returns_flattened_dataframe(self) -> None:
        """Test that to_dataframe returns a flattened DataFrame."""
        import pandas as pd

        from bcra_connector.principales_variables import DatosVariable

        datos = DatosVariable.from_dict(DATOS_VARIABLE_DATA)
        df = datos.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["idVariable", "fecha", "valor"]
        assert df.iloc[0]["valor"] == 100.0
        assert df.iloc[2]["valor"] == 102.0


class TestEntidadToDataframe:
    """Tests for Entidad.to_dataframe() method."""

    def test_to_dataframe_returns_dataframe(self) -> None:
        """Test that to_dataframe returns a pandas DataFrame."""
        import pandas as pd

        from bcra_connector.cheques import Entidad

        entidad = Entidad.from_dict(ENTIDAD_DATA)
        df = entidad.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["codigoEntidad"] == 123
        assert df.iloc[0]["denominacion"] == "Banco Test"


class TestChequeToDataframe:
    """Tests for Cheque.to_dataframe() method."""

    def test_to_dataframe_returns_flattened_dataframe(self) -> None:
        """Test that to_dataframe returns flattened check data."""
        import pandas as pd

        from bcra_connector.cheques import Cheque

        cheque = Cheque.from_dict(CHEQUE_DATA)
        df = cheque.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # Two detalles
        assert df.iloc[0]["numeroCheque"] == 12345
        assert df.iloc[0]["sucursal"] == 1
        assert df.iloc[1]["sucursal"] == 2

    def test_to_dataframe_with_no_detalles(self) -> None:
        """Test to_dataframe when cheque has no detalles."""
        import pandas as pd

        from bcra_connector.cheques import Cheque

        data = {**CHEQUE_DATA, "detalles": []}
        cheque = Cheque.from_dict(data)
        df = cheque.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["sucursal"] is None


class TestCotizacionFechaToDataframe:
    """Tests for CotizacionFecha.to_dataframe() method."""

    def test_to_dataframe_returns_flattened_dataframe(self) -> None:
        """Test that to_dataframe returns flattened exchange rate data."""
        import pandas as pd

        from bcra_connector.estadisticas_cambiarias import CotizacionFecha

        cot = CotizacionFecha.from_dict(COTIZACION_FECHA_DATA)
        df = cot.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["codigoMoneda"] == "USD"
        assert df.iloc[1]["codigoMoneda"] == "EUR"
        assert df.iloc[0]["tipoCotizacion"] == 850.0
