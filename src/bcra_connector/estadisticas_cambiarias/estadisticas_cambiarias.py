"""
Data models for the BCRA Currency Exchange Statistics API.
Provides classes for currency quotations, historical data, and response handling.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import Metadata, optional, require, to_dataframe

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class Divisa:
    """
    Represents a currency.

    :param codigo: The currency code (ISO)
    :param denominacion: The currency name
    """

    codigo: str
    denominacion: str

    def __post_init__(self) -> None:
        """Validate instance after initialization."""
        if not self.codigo.strip():
            raise ValueError("Currency code cannot be empty")
        if not self.denominacion.strip():
            raise ValueError("Currency name cannot be empty")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Divisa":
        """Create a Divisa instance from a dictionary."""
        return cls(
            codigo=require(data, "codigo", str),
            denominacion=require(data, "denominacion", str),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Divisa instance to a dictionary."""
        return {"codigo": self.codigo, "denominacion": self.denominacion}


@dataclass
class CotizacionDetalle:
    """
    Represents details of a currency quotation.

    :param codigo_moneda: The currency code
    :param descripcion: The currency description
    :param tipo_pase: The exchange rate
    :param tipo_cotizacion: The quotation type
    """

    codigo_moneda: str
    descripcion: str
    tipo_pase: float
    tipo_cotizacion: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CotizacionDetalle":
        """Create a CotizacionDetalle instance from a dictionary."""
        return cls(
            codigo_moneda=require(data, "codigoMoneda", str),
            descripcion=require(data, "descripcion", str),
            tipo_pase=require(data, "tipoPase", float),
            tipo_cotizacion=require(data, "tipoCotizacion", float),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the CotizacionDetalle instance to a dictionary."""
        return {
            "codigoMoneda": self.codigo_moneda,
            "descripcion": self.descripcion,
            "tipoPase": self.tipo_pase,
            "tipoCotizacion": self.tipo_cotizacion,
        }


@dataclass
class CotizacionFecha:
    """
    Represents currency quotations for a specific date.

    :param fecha: The date of the quotations
    :param detalle: List of quotation details
    """

    fecha: Optional[date]
    detalle: List[CotizacionDetalle]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CotizacionFecha":
        """Create a CotizacionFecha instance from a dictionary."""
        return cls(
            fecha=optional(data, "fecha", date),
            detalle=[
                CotizacionDetalle.from_dict(d) for d in require(data, "detalle", list)
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the CotizacionFecha instance to a dictionary."""
        return {
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "detalle": [d.to_dict() for d in self.detalle],
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the CotizacionFecha instance to a pandas DataFrame.

        Returns a DataFrame with exchange rate information for each currency.
        Columns: fecha, codigoMoneda, descripcion, tipoPase, tipoCotizacion.

        Requires pandas: ``pip install bcra-connector[pandas]``

        :return: DataFrame with exchange rate data.
        :raises ImportError: If pandas is not installed.
        """
        rows = [
            {
                "fecha": self.fecha,
                "codigoMoneda": d.codigo_moneda,
                "descripcion": d.descripcion,
                "tipoPase": d.tipo_pase,
                "tipoCotizacion": d.tipo_cotizacion,
            }
            for d in self.detalle
        ]
        return to_dataframe(rows)


@dataclass
class DivisaResponse:
    """
    Represents the response for the Divisas endpoint.

    :param status: The HTTP status code
    :param results: List of Divisa objects
    """

    status: int
    results: List[Divisa]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DivisaResponse":
        """Create a DivisaResponse instance from a dictionary."""
        return cls(
            status=require(data, "status", int),
            results=[Divisa.from_dict(d) for d in require(data, "results", list)],
        )


@dataclass
class CotizacionResponse:
    """
    Represents the response for the Cotizaciones endpoint.

    :param status: The HTTP status code
    :param results: CotizacionFecha object
    """

    status: int
    results: CotizacionFecha

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CotizacionResponse":
        """Create a CotizacionResponse instance from a dictionary."""
        return cls(
            status=require(data, "status", int),
            results=CotizacionFecha.from_dict(require(data, "results", dict)),
        )


@dataclass
class CotizacionesResponse:
    """
    Represents the response for the Cotizaciones/{codMoneda} endpoint.

    :param status: The HTTP status code
    :param metadata: Metadata about the response
    :param results: List of CotizacionFecha objects
    """

    status: int
    metadata: Metadata
    results: List[CotizacionFecha]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CotizacionesResponse":
        """Create a CotizacionesResponse instance from a dictionary."""
        return cls(
            status=require(data, "status", int),
            metadata=Metadata.from_dict(require(data, "metadata", dict)),
            results=[
                CotizacionFecha.from_dict(d) for d in require(data, "results", list)
            ],
        )


@dataclass
class ErrorResponse:
    """
    Represents an error response from the API.

    :param status: The HTTP status code
    :param error_messages: List of error messages
    """

    status: int
    error_messages: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorResponse":
        """Create an ErrorResponse instance from a dictionary."""
        return cls(
            status=require(data, "status", int),
            error_messages=require(data, "errorMessages", list),
        )
