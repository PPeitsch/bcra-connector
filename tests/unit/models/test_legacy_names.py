"""The pre-1.0 camelCase names keep working, with a warning (issue #135)."""

from datetime import date

import pytest

from bcra_connector.principales_variables import DatosVariable, PrincipalesVariables

ALIASES = [
    ("idVariable", "id_variable", 1),
    ("tipoSerie", "tipo_serie", "Diaria"),
    ("unidadExpresion", "unidad_expresion", "Millones"),
    ("primerFechaInformada", "primer_fecha_informada", date(2020, 1, 1)),
    ("ultFechaInformada", "ult_fecha_informada", date(2024, 3, 5)),
    ("ultValorInformado", "ult_valor_informado", 100.0),
]


@pytest.fixture
def variable() -> PrincipalesVariables:
    return PrincipalesVariables(
        id_variable=1,
        descripcion="Reservas",
        tipo_serie="Diaria",
        unidad_expresion="Millones",
        primer_fecha_informada=date(2020, 1, 1),
        ult_fecha_informada=date(2024, 3, 5),
        ult_valor_informado=100.0,
    )


class TestReading:
    """Reading the old name warns and returns the new attribute."""

    @pytest.mark.parametrize("old,new,_", ALIASES, ids=[a[0] for a in ALIASES])
    def test_old_name_reads_the_new_field(
        self, variable: PrincipalesVariables, old: str, new: str, _: object
    ) -> None:
        with pytest.warns(DeprecationWarning, match=f"use .{new} instead"):
            value = getattr(variable, old)
        assert value == getattr(variable, new)

    def test_warning_names_the_class(self, variable: PrincipalesVariables) -> None:
        with pytest.warns(
            DeprecationWarning, match="PrincipalesVariables.idVariable is deprecated"
        ):
            variable.idVariable

    def test_new_name_does_not_warn(
        self, variable: PrincipalesVariables, recwarn: pytest.WarningsRecorder
    ) -> None:
        assert variable.id_variable == 1
        assert len(recwarn) == 0

    def test_a_typo_is_still_a_typo(self, variable: PrincipalesVariables) -> None:
        with pytest.raises(AttributeError, match="idVariabel"):
            variable.idVariabel

    def test_datos_variable_too(self) -> None:
        datos = DatosVariable(id_variable=7, detalle=[])
        with pytest.warns(DeprecationWarning, match="use .id_variable instead"):
            assert datos.idVariable == 7


class TestConstructing:
    """The old name is still accepted as a keyword argument."""

    @pytest.mark.parametrize("old,new,value", ALIASES, ids=[a[0] for a in ALIASES])
    def test_old_keyword_sets_the_new_field(
        self, old: str, new: str, value: object
    ) -> None:
        kwargs = {"id_variable": 1, old: value}
        with pytest.warns(DeprecationWarning, match=f"use .{new} instead"):
            variable = PrincipalesVariables(**kwargs)
        assert getattr(variable, new) == value

    def test_positional_arguments_still_work(self) -> None:
        assert PrincipalesVariables(1, "Reservas").id_variable == 1

    def test_unknown_keyword_still_raises(self) -> None:
        with pytest.raises(TypeError):
            PrincipalesVariables(idVariabel=1)


class TestDatosVariableEquality:
    """`__eq__` compares every field, not just the id (issue #135)."""

    def test_same_id_different_detalle_differ(self) -> None:
        from bcra_connector.principales_variables import DetalleMonetaria

        point = DetalleMonetaria(fecha=date(2024, 1, 1), valor=1.0)
        assert DatosVariable(id_variable=1, detalle=[point]) != DatosVariable(
            id_variable=1, detalle=[]
        )

    def test_identical_instances_are_equal(self) -> None:
        assert DatosVariable(id_variable=1, detalle=[]) == DatosVariable(
            id_variable=1, detalle=[]
        )

    def test_other_types_are_not_equal(self) -> None:
        assert DatosVariable(id_variable=1, detalle=[]) != "not a DatosVariable"
