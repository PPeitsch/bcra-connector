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
        pd = pytest.importorskip("pandas")

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
        pd = pytest.importorskip("pandas")

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
        pd = pytest.importorskip("pandas")

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
        pd = pytest.importorskip("pandas")

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
        pd = pytest.importorskip("pandas")

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
        pd = pytest.importorskip("pandas")

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
        pd = pytest.importorskip("pandas")

        from bcra_connector.estadisticas_cambiarias import CotizacionFecha

        cot = CotizacionFecha.from_dict(COTIZACION_FECHA_DATA)
        df = cot.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["codigoMoneda"] == "USD"
        assert df.iloc[1]["codigoMoneda"] == "EUR"
        assert df.iloc[0]["tipoCotizacion"] == 850.0


DIVISA_DATA = {"codigo": "USD", "denominacion": "DOLAR ESTADOUNIDENSE"}

DEUDOR_DATA = {
    "identificacion": 20000000001,
    "denominacion": "Test SA",
    "periodos": [
        {
            "periodo": "202401",
            "entidades": [
                {
                    "entidad": "BANCO TEST",
                    "situacion": 1,
                    "monto": 100.0,
                    "enRevision": False,
                    "procesoJud": False,
                }
            ],
        }
    ],
}


class TestModuleLevelToDataframe:
    """`to_dataframe(rows)` is the one way the library hands data to pandas."""

    def test_it_is_exported(self) -> None:
        import bcra_connector

        assert "to_dataframe" in bcra_connector.__all__

    def test_one_row_per_model(self) -> None:
        pd = pytest.importorskip("pandas")

        from bcra_connector import to_dataframe
        from bcra_connector.principales_variables import DetalleMonetaria

        rows = [
            DetalleMonetaria.from_dict({"fecha": "2024-01-01", "valor": 1.0}),
            DetalleMonetaria.from_dict({"fecha": "2024-01-02", "valor": 2.0}),
        ]
        df = to_dataframe(rows)

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["fecha", "valor"]
        assert df["valor"].tolist() == [1.0, 2.0]

    def test_it_takes_any_iterable(self) -> None:
        """A generator, so a filtered selection needs no intermediate list."""
        pytest.importorskip("pandas")

        from bcra_connector import to_dataframe
        from bcra_connector.principales_variables import DetalleMonetaria

        rows = [
            DetalleMonetaria.from_dict({"fecha": "2024-01-01", "valor": 1.0}),
            DetalleMonetaria.from_dict({"fecha": "2024-01-02", "valor": 200.0}),
        ]
        df = to_dataframe(row for row in rows if row.valor > 100)

        assert df["valor"].tolist() == [200.0]

    def test_plain_dicts_pass_through(self) -> None:
        pytest.importorskip("pandas")

        from bcra_connector import to_dataframe

        assert to_dataframe([{"a": 1}, {"a": 2}])["a"].tolist() == [1, 2]

    def test_empty_input_gives_an_empty_frame(self) -> None:
        pd = pytest.importorskip("pandas")

        from bcra_connector import to_dataframe

        df = to_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_without_pandas_it_names_the_extra(self) -> None:
        from bcra_connector import to_dataframe

        with patch.dict("sys.modules", {"pandas": None}):
            with pytest.raises(ImportError, match=r"bcra-connector\[pandas\]"):
                to_dataframe([])


class TestDateColumns:
    """Dates are `datetime64[ns]`, whichever call built the frame (issue #147)."""

    def _frames(self) -> dict:
        from bcra_connector.cheques import Cheque
        from bcra_connector.estadisticas_cambiarias import CotizacionFecha
        from bcra_connector.models import Page
        from bcra_connector.principales_variables import (
            DatosVariable,
            DetalleMonetaria,
            PrincipalesVariables,
        )

        detalle = DetalleMonetaria.from_dict(DETALLE_MONETARIA_DATA)
        variable = PrincipalesVariables.from_dict(PRINCIPALES_VARIABLES_DATA)
        return {
            # rows built from to_dict(), so the wire format's ISO strings
            "PrincipalesVariables": (variable.to_dataframe(), "ultFechaInformada"),
            "DetalleMonetaria": (detalle.to_dataframe(), "fecha"),
            "Page[PrincipalesVariables]": (
                Page([variable]).to_dataframe(),
                "ultFechaInformada",
            ),
            "Page[DetalleMonetaria]": (Page([detalle]).to_dataframe(), "fecha"),
            # rows built by hand, so real date objects
            "DatosVariable": (
                DatosVariable.from_dict(DATOS_VARIABLE_DATA).to_dataframe(),
                "fecha",
            ),
            "Cheque": (
                Cheque.from_dict(CHEQUE_DATA).to_dataframe(),
                "fechaProcesamiento",
            ),
            "CotizacionFecha": (
                CotizacionFecha.from_dict(COTIZACION_FECHA_DATA).to_dataframe(),
                "fecha",
            ),
        }

    def test_every_call_agrees_on_the_dtype(self) -> None:
        """Before #147: `str` in four of these, `object` in the other three."""
        pytest.importorskip("pandas")

        for label, (df, column) in self._frames().items():
            assert str(df[column].dtype) == "datetime64[ns]", label

    def test_the_datetime_accessor_works(self) -> None:
        pytest.importorskip("pandas")

        from bcra_connector.principales_variables import DatosVariable

        df = DatosVariable.from_dict(DATOS_VARIABLE_DATA).to_dataframe()
        assert df["fecha"].dt.day.tolist() == [1, 2, 3]

    def test_a_null_date_becomes_nat(self) -> None:
        pd = pytest.importorskip("pandas")

        from bcra_connector.principales_variables import PrincipalesVariables

        df = PrincipalesVariables.from_dict(
            {"idVariable": 1, "primerFechaInformada": "2020-01-01"}
        ).to_dataframe()
        assert "ultFechaInformada" not in df.columns
        df = pd.concat(
            [
                df,
                PrincipalesVariables.from_dict(
                    {"idVariable": 2, "ultFechaInformada": "2024-01-01"}
                ).to_dataframe(),
            ]
        )
        assert df["primerFechaInformada"].isna().sum() == 1

    def test_a_column_of_plain_strings_is_left_alone(self) -> None:
        """Only a column that is *all* dates is converted."""
        pytest.importorskip("pandas")

        from bcra_connector import to_dataframe

        df = to_dataframe([{"fecha": "2024-01-01"}, {"fecha": "not a date"}])
        assert str(df["fecha"].dtype) in ("object", "str")

    def test_a_period_is_not_a_date(self) -> None:
        """`periodo` is YYYYMM, which is not an ISO date and must stay a string."""
        pytest.importorskip("pandas")

        from bcra_connector.central_deudores import Deudor

        df = Deudor.from_dict(DEUDOR_DATA).to_dataframe()
        assert df["periodo"].tolist() == ["202401"]
        assert str(df["periodo"].dtype) in ("object", "str")


class TestMissingToDict:
    """`Divisa` and `CotizacionDetalle` can describe themselves now (issue #147)."""

    def test_divisa_to_dict(self) -> None:
        from bcra_connector.estadisticas_cambiarias import Divisa

        assert Divisa.from_dict(DIVISA_DATA).to_dict() == DIVISA_DATA

    def test_cotizacion_detalle_to_dict(self) -> None:
        from bcra_connector.estadisticas_cambiarias import CotizacionDetalle

        block = COTIZACION_FECHA_DATA["detalle"][0]
        assert CotizacionDetalle.from_dict(block).to_dict() == block

    def test_a_page_of_divisas_has_real_columns(self) -> None:
        """Without to_dict() the dataclass itself landed in the cell."""
        pytest.importorskip("pandas")

        from bcra_connector.estadisticas_cambiarias import Divisa
        from bcra_connector.models import Page

        df = Page([Divisa.from_dict(DIVISA_DATA)]).to_dataframe()
        assert list(df.columns) == ["codigo", "denominacion"]
        assert df.iloc[0]["codigo"] == "USD"
