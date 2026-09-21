"""
Data models for BCRA's Central de Deudores API (v1.0).
Defines dataclasses for debtor information, debts, and rejected checks.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import optional, require, to_dataframe

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class EntidadDeuda:
    """
    Represents a debt record from a financial entity.

    :param entidad: Name of the financial entity
    :param situacion: Debtor classification (1-5 scale, None if not applicable)
    :param monto: Amount in thousands of pesos
    :param en_revision: Whether the information is under review (Law 25.326)
    :param proceso_jud: Whether the information is under judicial process
    """

    entidad: str
    situacion: Optional[int]
    monto: float
    en_revision: bool
    proceso_jud: bool

    def __post_init__(self) -> None:
        """Validate instance after initialization."""
        if self.situacion is not None and not 1 <= self.situacion <= 5:
            raise ValueError("Situacion must be between 1 and 5 when present")
        if self.monto < 0:
            raise ValueError("Monto must be non-negative")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntidadDeuda":
        """Create an EntidadDeuda instance from a dictionary."""
        return cls(
            entidad=require(data, "entidad", str),
            # The API reports "no situation" as 0, which __post_init__ rejects
            situacion=optional(data, "situacion", int) or None,
            monto=require(data, "monto", float),
            en_revision=optional(data, "enRevision", bool, default=False),
            proceso_jud=optional(data, "procesoJud", bool, default=False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "entidad": self.entidad,
            "situacion": self.situacion if self.situacion is not None else 0,
            "monto": self.monto,
            "enRevision": self.en_revision,
            "procesoJud": self.proceso_jud,
        }


@dataclass
class Periodo:
    """
    Represents a period with associated entity debts.

    :param periodo: Period in YYYYMM format
    :param entidades: List of entity debt records
    """

    periodo: str
    entidades: List[EntidadDeuda]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Periodo":
        """Create a Periodo instance from a dictionary."""
        entidades = [
            EntidadDeuda.from_dict(e)
            for e in optional(data, "entidades", list, default=[])
        ]
        return cls(periodo=require(data, "periodo", str), entidades=entidades)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "periodo": self.periodo,
            "entidades": [e.to_dict() for e in self.entidades],
        }


@dataclass
class Deudor:
    """
    Represents a debtor profile with debt information.

    :param identificacion: CUIT/CUIL/CDI (11 digits)
    :param denominacion: Name or company name from AFIP registry
    :param periodos: List of periods with debt information
    """

    identificacion: int
    denominacion: str
    periodos: List[Periodo]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deudor":
        """Create a Deudor instance from a dictionary."""
        periodos = [
            Periodo.from_dict(p) for p in optional(data, "periodos", list, default=[])
        ]
        return cls(
            identificacion=require(data, "identificacion", int),
            denominacion=require(data, "denominacion", str),
            periodos=periodos,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "identificacion": self.identificacion,
            "denominacion": self.denominacion,
            "periodos": [p.to_dict() for p in self.periodos],
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the debtor information to a pandas DataFrame.

        Returns a flattened DataFrame with columns: identificacion, denominacion,
        periodo, entidad, situacion, monto, enRevision, procesoJud.

        Requires pandas: ``pip install bcra-connector[pandas]``

        :return: DataFrame with all debt records.
        :raises ImportError: If pandas is not installed.
        """
        rows = []
        for periodo in self.periodos:
            for entidad in periodo.entidades:
                rows.append(
                    {
                        "identificacion": self.identificacion,
                        "denominacion": self.denominacion,
                        "periodo": periodo.periodo,
                        "entidad": entidad.entidad,
                        "situacion": entidad.situacion,
                        "monto": entidad.monto,
                        "enRevision": entidad.en_revision,
                        "procesoJud": entidad.proceso_jud,
                    }
                )
        if not rows:
            rows = [
                {
                    "identificacion": self.identificacion,
                    "denominacion": self.denominacion,
                    "periodo": None,
                    "entidad": None,
                    "situacion": None,
                    "monto": None,
                    "enRevision": None,
                    "procesoJud": None,
                }
            ]
        return to_dataframe(rows)


@dataclass
class ChequeRechazado:
    """
    Represents a rejected check detail.

    :param nro_cheque: Check number
    :param fecha_rechazo: Rejection date
    :param monto: Check amount
    :param fecha_pago: Payment date (if check was cleared)
    :param fecha_pago_multa: Fine payment date
    :param estado_multa: Fine status (IMPAGA, SUSPENDIDO, etc.)
    :param cta_personal: Whether it's a personal account
    :param denom_juridica: Company name if linked to legal entity
    :param en_revision: Whether under review
    :param proceso_jud: Whether under judicial process
    """

    nro_cheque: int
    fecha_rechazo: date
    monto: float
    fecha_pago: Optional[date]
    fecha_pago_multa: Optional[date]
    estado_multa: Optional[str]
    cta_personal: bool
    denom_juridica: Optional[str]
    en_revision: bool
    proceso_jud: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChequeRechazado":
        """Create a ChequeRechazado instance from a dictionary."""
        return cls(
            nro_cheque=require(data, "nroCheque", int),
            fecha_rechazo=require(data, "fechaRechazo", date),
            monto=require(data, "monto", float),
            fecha_pago=optional(data, "fechaPago", date),
            fecha_pago_multa=optional(data, "fechaPagoMulta", date),
            estado_multa=optional(data, "estadoMulta", str),
            cta_personal=optional(data, "ctaPersonal", bool, default=False),
            denom_juridica=optional(data, "denomJuridica", str),
            en_revision=optional(data, "enRevision", bool, default=False),
            proceso_jud=optional(data, "procesoJud", bool, default=False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "nroCheque": self.nro_cheque,
            "fechaRechazo": self.fecha_rechazo.isoformat(),
            "monto": self.monto,
            "fechaPago": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "fechaPagoMulta": (
                self.fecha_pago_multa.isoformat() if self.fecha_pago_multa else None
            ),
            "estadoMulta": self.estado_multa,
            "ctaPersonal": self.cta_personal,
            "denomJuridica": self.denom_juridica,
            "enRevision": self.en_revision,
            "procesoJud": self.proceso_jud,
        }


@dataclass
class EntidadCheques:
    """
    Represents checks grouped by entity within a causal.

    :param entidad: Entity grouping number
    :param detalle: List of rejected checks
    """

    entidad: int
    detalle: List[ChequeRechazado]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntidadCheques":
        """Create an EntidadCheques instance from a dictionary."""
        detalle = [
            ChequeRechazado.from_dict(c)
            for c in optional(data, "detalle", list, default=[])
        ]
        return cls(entidad=require(data, "entidad", int), detalle=detalle)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "entidad": self.entidad,
            "detalle": [c.to_dict() for c in self.detalle],
        }


@dataclass
class CausalCheques:
    """
    Represents checks grouped by rejection reason (causal).

    :param causal: Rejection reason (e.g., "SIN FONDOS", "DEFECTOS FORMALES")
    :param entidades: List of entities with rejected checks
    """

    causal: str
    entidades: List[EntidadCheques]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CausalCheques":
        """Create a CausalCheques instance from a dictionary."""
        entidades = [
            EntidadCheques.from_dict(e)
            for e in optional(data, "entidades", list, default=[])
        ]
        return cls(causal=require(data, "causal", str), entidades=entidades)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "causal": self.causal,
            "entidades": [e.to_dict() for e in self.entidades],
        }


@dataclass
class ChequesRechazados:
    """
    Represents rejected checks response for a debtor.

    :param identificacion: CUIT/CUIL/CDI (11 digits)
    :param denominacion: Name or company name from AFIP registry
    :param causales: List of causals with rejected checks
    """

    identificacion: int
    denominacion: str
    causales: List[CausalCheques]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChequesRechazados":
        """Create a ChequesRechazados instance from a dictionary."""
        causales = [
            CausalCheques.from_dict(c)
            for c in optional(data, "causales", list, default=[])
        ]
        return cls(
            identificacion=require(data, "identificacion", int),
            denominacion=require(data, "denominacion", str),
            causales=causales,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "identificacion": self.identificacion,
            "denominacion": self.denominacion,
            "causales": [c.to_dict() for c in self.causales],
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert rejected checks to a pandas DataFrame.

        Returns a flattened DataFrame with all check details.

        Requires pandas: ``pip install bcra-connector[pandas]``

        :return: DataFrame with all rejected check records.
        :raises ImportError: If pandas is not installed.
        """
        rows = []
        for causal in self.causales:
            for entidad in causal.entidades:
                for cheque in entidad.detalle:
                    rows.append(
                        {
                            "identificacion": self.identificacion,
                            "denominacion": self.denominacion,
                            "causal": causal.causal,
                            "entidad": entidad.entidad,
                            "nroCheque": cheque.nro_cheque,
                            "fechaRechazo": cheque.fecha_rechazo,
                            "monto": cheque.monto,
                            "fechaPago": cheque.fecha_pago,
                            "fechaPagoMulta": cheque.fecha_pago_multa,
                            "estadoMulta": cheque.estado_multa,
                            "ctaPersonal": cheque.cta_personal,
                            "denomJuridica": cheque.denom_juridica,
                            "enRevision": cheque.en_revision,
                            "procesoJud": cheque.proceso_jud,
                        }
                    )
        if not rows:
            rows = [
                {
                    "identificacion": self.identificacion,
                    "denominacion": self.denominacion,
                    "causal": None,
                    "entidad": None,
                    "nroCheque": None,
                    "fechaRechazo": None,
                    "monto": None,
                    "fechaPago": None,
                    "fechaPagoMulta": None,
                    "estadoMulta": None,
                    "ctaPersonal": None,
                    "denomJuridica": None,
                    "enRevision": None,
                    "procesoJud": None,
                }
            ]
        return to_dataframe(rows)
