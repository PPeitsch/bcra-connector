"""
Unit tests for Central de Deudores API models.
Tests dataclasses: EntidadDeuda, Periodo, Deudor, ChequeRechazado, EntidadCheques,
CausalCheques, ChequesRechazados.
"""

from datetime import date

import pytest

from bcra_connector.central_deudores import (
    CausalCheques,
    ChequeRechazado,
    ChequesRechazados,
    Deudor,
    EntidadCheques,
    EntidadDeuda,
    Periodo,
)

# One entity of a real Deudas/{id} response (2026-09-28), issue #179
DEUDA_ACTUAL = {
    "entidad": "BANCO DE LA PROVINCIA DE BUENOS AIRES",
    "situacion": 1,
    "fechaSit1": "2025-12-30",
    "monto": 27157.0,
    "diasAtrasoPago": 0,
    "refinanciaciones": False,
    "recategorizacionOblig": False,
    "situacionJuridica": False,
    "irrecDisposicionTecnica": False,
    "enRevision": False,
    "procesoJud": False,
}

CLASSIFICATION_COLUMNS = [
    "fechaSit1",
    "diasAtrasoPago",
    "refinanciaciones",
    "recategorizacionOblig",
    "situacionJuridica",
    "irrecDisposicionTecnica",
]


class TestEntidadDeuda:
    """Tests for EntidadDeuda dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating EntidadDeuda from valid dict."""
        data = {
            "entidad": "BANCO DE LA NACION ARGENTINA",
            "situacion": 1,
            "monto": 35.0,
            "enRevision": False,
            "procesoJud": False,
        }
        entidad = EntidadDeuda.from_dict(data)
        assert entidad.entidad == "BANCO DE LA NACION ARGENTINA"
        assert entidad.situacion == 1
        assert entidad.monto == 35.0
        assert entidad.en_revision is False
        assert entidad.proceso_jud is False

    def test_from_dict_defaults(self) -> None:
        """Test defaults for optional boolean fields."""
        data = {"entidad": "BANCO TEST", "situacion": 2, "monto": 100.0}
        entidad = EntidadDeuda.from_dict(data)
        assert entidad.en_revision is False
        assert entidad.proceso_jud is False

    def test_to_dict(self) -> None:
        """Test converting to dict."""
        entidad = EntidadDeuda(
            entidad="TEST BANK",
            situacion=3,
            monto=500.0,
            en_revision=True,
            proceso_jud=False,
        )
        result = entidad.to_dict()
        assert result["entidad"] == "TEST BANK"
        assert result["situacion"] == 3
        assert result["monto"] == 500.0
        assert result["enRevision"] is True
        assert result["procesoJud"] is False

    def test_invalid_situacion(self) -> None:
        """Test validation of situacion range."""
        with pytest.raises(ValueError, match="Situacion must be between 1 and 5"):
            EntidadDeuda(
                entidad="TEST",
                situacion=0,
                monto=100.0,
                en_revision=False,
                proceso_jud=False,
            )

    def test_invalid_situacion_too_high(self) -> None:
        """Test validation of situacion max value."""
        with pytest.raises(ValueError, match="Situacion must be between 1 and 5"):
            EntidadDeuda(
                entidad="TEST",
                situacion=6,
                monto=100.0,
                en_revision=False,
                proceso_jud=False,
            )

    def test_situacion_none_allowed(self) -> None:
        """Test that situacion can be None."""
        entidad = EntidadDeuda(
            entidad="TEST",
            situacion=None,
            monto=100.0,
            en_revision=False,
            proceso_jud=False,
        )
        assert entidad.situacion is None

    def test_negative_monto(self) -> None:
        """Test validation of negative monto."""
        with pytest.raises(ValueError, match="Monto must be non-negative"):
            EntidadDeuda(
                entidad="TEST",
                situacion=1,
                monto=-10.0,
                en_revision=False,
                proceso_jud=False,
            )

    def test_from_dict_reads_the_classification_fields(self) -> None:
        """The six fields Deudas returns and 1.1 dropped (issue #179)."""
        entidad = EntidadDeuda.from_dict(DEUDA_ACTUAL)
        assert entidad.fecha_sit1 == date(2025, 12, 30)
        assert entidad.dias_atraso_pago is None  # 0 means "not applicable"
        assert entidad.refinanciaciones is False
        assert entidad.recategorizacion_oblig is False
        assert entidad.situacion_juridica is False
        assert entidad.irrec_disposicion_tecnica is False

    def test_from_dict_reads_flags_set_to_true(self) -> None:
        data = {
            **DEUDA_ACTUAL,
            "situacion": 4,
            "fechaSit1": None,
            "diasAtrasoPago": 187,
            "refinanciaciones": True,
            "recategorizacionOblig": True,
            "situacionJuridica": True,
            "irrecDisposicionTecnica": True,
        }
        entidad = EntidadDeuda.from_dict(data)
        assert entidad.fecha_sit1 is None
        assert entidad.dias_atraso_pago == 187
        assert entidad.refinanciaciones is True
        assert entidad.recategorizacion_oblig is True
        assert entidad.situacion_juridica is True
        assert entidad.irrec_disposicion_tecnica is True

    def test_from_dict_without_the_classification_fields(self) -> None:
        """DeudasHistoricas (and older responses) don't send them: defaults."""
        entidad = EntidadDeuda.from_dict(
            {"entidad": "BANCO TEST", "situacion": 2, "monto": 100.0}
        )
        assert entidad.fecha_sit1 is None
        assert entidad.dias_atraso_pago is None
        assert entidad.refinanciaciones is False
        assert entidad.recategorizacion_oblig is False
        assert entidad.situacion_juridica is False
        assert entidad.irrec_disposicion_tecnica is False

    def test_to_dict_round_trips_the_api_payload(self) -> None:
        assert EntidadDeuda.from_dict(DEUDA_ACTUAL).to_dict() == DEUDA_ACTUAL

    def test_positional_construction_still_works(self) -> None:
        """The new fields are trailing with defaults: 1.x callers keep working."""
        entidad = EntidadDeuda("TEST", 1, 10.0, False, False)
        assert entidad.fecha_sit1 is None
        assert entidad.situacion_juridica is False

    def test_negative_dias_atraso_pago(self) -> None:
        with pytest.raises(ValueError, match="Dias atraso pago must be non-negative"):
            EntidadDeuda(
                entidad="TEST",
                situacion=3,
                monto=10.0,
                en_revision=False,
                proceso_jud=False,
                dias_atraso_pago=-1,
            )


class TestPeriodo:
    """Tests for Periodo dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating Periodo from valid dict."""
        data = {
            "periodo": "202403",
            "entidades": [
                {"entidad": "BANCO A", "situacion": 1, "monto": 100.0},
                {"entidad": "BANCO B", "situacion": 2, "monto": 200.0},
            ],
        }
        periodo = Periodo.from_dict(data)
        assert periodo.periodo == "202403"
        assert len(periodo.entidades) == 2
        assert periodo.entidades[0].entidad == "BANCO A"

    def test_from_dict_empty_entidades(self) -> None:
        """Test creating Periodo with no entidades."""
        data = {"periodo": "202401", "entidades": []}
        periodo = Periodo.from_dict(data)
        assert periodo.periodo == "202401"
        assert len(periodo.entidades) == 0

    def test_to_dict(self) -> None:
        """Test converting to dict."""
        periodo = Periodo(
            periodo="202412",
            entidades=[
                EntidadDeuda(
                    entidad="BANK",
                    situacion=1,
                    monto=50.0,
                    en_revision=False,
                    proceso_jud=False,
                )
            ],
        )
        result = periodo.to_dict()
        assert result["periodo"] == "202412"
        assert len(result["entidades"]) == 1


class TestDeudor:
    """Tests for Deudor dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating Deudor from valid dict."""
        data = {
            "identificacion": 20123456789,
            "denominacion": "JUAN PEREZ",
            "periodos": [
                {
                    "periodo": "202403",
                    "entidades": [
                        {"entidad": "BANCO A", "situacion": 1, "monto": 100.0}
                    ],
                }
            ],
        }
        deudor = Deudor.from_dict(data)
        assert deudor.identificacion == 20123456789
        assert deudor.denominacion == "JUAN PEREZ"
        assert len(deudor.periodos) == 1

    def test_to_dict(self) -> None:
        """Test converting to dict."""
        deudor = Deudor(
            identificacion=30123456789,
            denominacion="EMPRESA SA",
            periodos=[],
        )
        result = deudor.to_dict()
        assert result["identificacion"] == 30123456789
        assert result["denominacion"] == "EMPRESA SA"

    def test_to_dataframe_with_data(self) -> None:
        """Test converting to DataFrame with data."""
        pytest.importorskip("pandas")
        deudor = Deudor(
            identificacion=20123456789,
            denominacion="TEST",
            periodos=[
                Periodo(
                    periodo="202403",
                    entidades=[
                        EntidadDeuda(
                            entidad="BANK1",
                            situacion=1,
                            monto=100.0,
                            en_revision=False,
                            proceso_jud=False,
                        ),
                        EntidadDeuda(
                            entidad="BANK2",
                            situacion=2,
                            monto=200.0,
                            en_revision=True,
                            proceso_jud=False,
                        ),
                    ],
                )
            ],
        )
        df = deudor.to_dataframe()
        assert len(df) == 2
        assert "identificacion" in df.columns
        assert "entidad" in df.columns
        assert df["monto"].sum() == 300.0

    def test_to_dataframe_empty(self) -> None:
        """Test converting empty deudor to DataFrame."""
        pytest.importorskip("pandas")
        deudor = Deudor(
            identificacion=20123456789,
            denominacion="TEST",
            periodos=[],
        )
        df = deudor.to_dataframe()
        assert len(df) == 1  # Single row with Nones
        assert df.iloc[0]["entidad"] is None
        for column in CLASSIFICATION_COLUMNS:
            assert df.iloc[0][column] is None, column

    def test_to_dataframe_has_the_classification_columns(self) -> None:
        pytest.importorskip("pandas")
        deudor = Deudor.from_dict(
            {
                "identificacion": 30500010912,
                "denominacion": "TEST SA",
                "periodos": [{"periodo": "202608", "entidades": [DEUDA_ACTUAL]}],
            }
        )
        df = deudor.to_dataframe()
        for column in CLASSIFICATION_COLUMNS:
            assert column in df.columns, column
        row = df.iloc[0]
        assert row["fechaSit1"].date() == date(2025, 12, 30)
        assert not row["refinanciaciones"]


class TestChequeRechazado:
    """Tests for ChequeRechazado dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating ChequeRechazado from valid dict."""
        data = {
            "nroCheque": 752395,
            "fechaRechazo": "2024-04-08",
            "monto": 115000.00,
            "fechaPago": None,
            "fechaPagoMulta": None,
            "estadoMulta": "IMPAGA",
            "ctaPersonal": False,
            "denomJuridica": "EMPRESA TEST S.R.L.",
            "enRevision": False,
            "procesoJud": False,
        }
        cheque = ChequeRechazado.from_dict(data)
        assert cheque.nro_cheque == 752395
        assert cheque.fecha_rechazo == date(2024, 4, 8)
        assert cheque.monto == 115000.00
        assert cheque.estado_multa == "IMPAGA"
        assert cheque.denom_juridica == "EMPRESA TEST S.R.L."

    def test_from_dict_with_dates(self) -> None:
        """Test with payment dates."""
        data = {
            "nroCheque": 123456,
            "fechaRechazo": "2024-01-15",
            "monto": 50000.0,
            "fechaPago": "2024-02-01",
            "fechaPagoMulta": "2024-02-15",
            "estadoMulta": None,
            "ctaPersonal": True,
            "denomJuridica": None,
            "enRevision": False,
            "procesoJud": False,
        }
        cheque = ChequeRechazado.from_dict(data)
        assert cheque.fecha_pago == date(2024, 2, 1)
        assert cheque.fecha_pago_multa == date(2024, 2, 15)
        assert cheque.cta_personal is True

    def test_to_dict(self) -> None:
        """Test converting to dict."""
        cheque = ChequeRechazado(
            nro_cheque=999999,
            fecha_rechazo=date(2024, 5, 1),
            monto=10000.0,
            fecha_pago=None,
            fecha_pago_multa=None,
            estado_multa="IMPAGA",
            cta_personal=True,
            denom_juridica=None,
            en_revision=False,
            proceso_jud=False,
        )
        result = cheque.to_dict()
        assert result["nroCheque"] == 999999
        assert result["fechaRechazo"] == "2024-05-01"
        assert result["fechaPago"] is None


class TestEntidadCheques:
    """Tests for EntidadCheques dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating EntidadCheques from valid dict."""
        data = {
            "entidad": 1,
            "detalle": [
                {
                    "nroCheque": 123,
                    "fechaRechazo": "2024-01-01",
                    "monto": 1000.0,
                    "fechaPago": None,
                    "fechaPagoMulta": None,
                    "estadoMulta": "IMPAGA",
                    "ctaPersonal": False,
                    "denomJuridica": None,
                    "enRevision": False,
                    "procesoJud": False,
                }
            ],
        }
        entidad = EntidadCheques.from_dict(data)
        assert entidad.entidad == 1
        assert len(entidad.detalle) == 1

    def test_to_dict(self) -> None:
        """Test converting EntidadCheques to dict."""
        entidad = EntidadCheques(
            entidad=1,
            detalle=[
                ChequeRechazado(
                    nro_cheque=123,
                    fecha_rechazo=date(2024, 1, 1),
                    monto=1000.0,
                    fecha_pago=None,
                    fecha_pago_multa=None,
                    estado_multa="IMPAGA",
                    cta_personal=False,
                    denom_juridica=None,
                    en_revision=False,
                    proceso_jud=False,
                )
            ],
        )
        result = entidad.to_dict()
        assert result["entidad"] == 1
        assert len(result["detalle"]) == 1
        assert result["detalle"][0]["nroCheque"] == 123


class TestCausalCheques:
    """Tests for CausalCheques dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating CausalCheques from valid dict."""
        data = {
            "causal": "SIN FONDOS",
            "entidades": [
                {
                    "entidad": 1,
                    "detalle": [
                        {
                            "nroCheque": 456,
                            "fechaRechazo": "2024-02-01",
                            "monto": 5000.0,
                            "fechaPago": None,
                            "fechaPagoMulta": None,
                            "estadoMulta": "IMPAGA",
                            "ctaPersonal": False,
                            "denomJuridica": None,
                            "enRevision": False,
                            "procesoJud": False,
                        }
                    ],
                }
            ],
        }
        causal = CausalCheques.from_dict(data)
        assert causal.causal == "SIN FONDOS"
        assert len(causal.entidades) == 1

    def test_to_dict(self) -> None:
        """Test converting CausalCheques to dict."""
        causal = CausalCheques(
            causal="SIN FONDOS",
            entidades=[
                EntidadCheques(
                    entidad=1,
                    detalle=[
                        ChequeRechazado(
                            nro_cheque=456,
                            fecha_rechazo=date(2024, 2, 1),
                            monto=5000.0,
                            fecha_pago=None,
                            fecha_pago_multa=None,
                            estado_multa="IMPAGA",
                            cta_personal=False,
                            denom_juridica=None,
                            en_revision=False,
                            proceso_jud=False,
                        )
                    ],
                )
            ],
        )
        result = causal.to_dict()
        assert result["causal"] == "SIN FONDOS"
        assert len(result["entidades"]) == 1
        assert result["entidades"][0]["entidad"] == 1


class TestChequesRechazados:
    """Tests for ChequesRechazados dataclass."""

    def test_from_dict_valid(self) -> None:
        """Test creating ChequesRechazados from valid dict."""
        data = {
            "identificacion": 20123456789,
            "denominacion": "PERSONA TEST",
            "causales": [
                {
                    "causal": "SIN FONDOS",
                    "entidades": [
                        {
                            "entidad": 1,
                            "detalle": [
                                {
                                    "nroCheque": 789,
                                    "fechaRechazo": "2024-03-01",
                                    "monto": 25000.0,
                                    "fechaPago": None,
                                    "fechaPagoMulta": None,
                                    "estadoMulta": "IMPAGA",
                                    "ctaPersonal": True,
                                    "denomJuridica": None,
                                    "enRevision": False,
                                    "procesoJud": False,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        cheques = ChequesRechazados.from_dict(data)
        assert cheques.identificacion == 20123456789
        assert cheques.denominacion == "PERSONA TEST"
        assert len(cheques.causales) == 1

    def test_to_dict(self) -> None:
        """Test converting ChequesRechazados to dict."""
        cheques = ChequesRechazados(
            identificacion=20123456789,
            denominacion="TEST",
            causales=[
                CausalCheques(
                    causal="SIN FONDOS",
                    entidades=[
                        EntidadCheques(
                            entidad=1,
                            detalle=[
                                ChequeRechazado(
                                    nro_cheque=789,
                                    fecha_rechazo=date(2024, 3, 1),
                                    monto=25000.0,
                                    fecha_pago=None,
                                    fecha_pago_multa=None,
                                    estado_multa="IMPAGA",
                                    cta_personal=True,
                                    denom_juridica=None,
                                    en_revision=False,
                                    proceso_jud=False,
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        result = cheques.to_dict()
        assert result["identificacion"] == 20123456789
        assert result["denominacion"] == "TEST"
        assert len(result["causales"]) == 1
        assert result["causales"][0]["causal"] == "SIN FONDOS"

    def test_to_dataframe_with_data(self) -> None:
        """Test converting to DataFrame with data."""
        pytest.importorskip("pandas")
        cheques = ChequesRechazados(
            identificacion=20123456789,
            denominacion="TEST",
            causales=[
                CausalCheques(
                    causal="SIN FONDOS",
                    entidades=[
                        EntidadCheques(
                            entidad=1,
                            detalle=[
                                ChequeRechazado(
                                    nro_cheque=111,
                                    fecha_rechazo=date(2024, 1, 1),
                                    monto=1000.0,
                                    fecha_pago=None,
                                    fecha_pago_multa=None,
                                    estado_multa="IMPAGA",
                                    cta_personal=True,
                                    denom_juridica=None,
                                    en_revision=False,
                                    proceso_jud=False,
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        df = cheques.to_dataframe()
        assert len(df) == 1
        assert "causal" in df.columns
        assert df.iloc[0]["nroCheque"] == 111

    def test_to_dataframe_empty(self) -> None:
        """Test empty cheques to DataFrame."""
        pytest.importorskip("pandas")
        cheques = ChequesRechazados(
            identificacion=20123456789,
            denominacion="TEST",
            causales=[],
        )
        df = cheques.to_dataframe()
        assert len(df) == 1  # Single row with Nones
        assert df.iloc[0]["causal"] is None
