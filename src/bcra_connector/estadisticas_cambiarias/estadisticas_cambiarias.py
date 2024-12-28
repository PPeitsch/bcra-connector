"""
Data models for the BCRA Currency Exchange Statistics API.
Provides classes for currency quotations, historical data, and response handling.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional


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
        return cls(codigo=data["codigo"], denominacion=data["denominacion"])


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
            codigo_moneda=data["codigoMoneda"],
            descripcion=data["descripcion"],
            tipo_pase=float(data["tipoPase"]),
            tipo_cotizacion=float(data["tipoCotizacion"]),
        )


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
            fecha=date.fromisoformat(data["fecha"]) if data["fecha"] else None,
            detalle=[CotizacionDetalle.from_dict(d) for d in data["detalle"]],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the CotizacionFecha instance to a dictionary."""
        return {
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "detalle": [
                {
                    "codigoMoneda": d.codigo_moneda,
                    "descripcion": d.descripcion,
                    "tipoPase": d.tipo_pase,
                    "tipoCotizacion": d.tipo_cotizacion,
                }
                for d in self.detalle
            ],
        }


@dataclass
class Resultset:
    """
    Represents metadata about the result set.

    :param count: The number of results
    :param offset: The offset of the results
    :param limit: The limit of the results
    """

    count: int
    offset: int
    limit: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resultset":
        """Create a Resultset instance from a dictionary."""
        return cls(count=data["count"], offset=data["offset"], limit=data["limit"])


@dataclass
class Metadata:
    """
    Represents metadata about the response.

    :param resultset: The resultset metadata
    """

    resultset: Resultset

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create a Metadata instance from a dictionary."""
        return cls(resultset=Resultset.from_dict(data["resultset"]))


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
            status=data["status"],
            results=[Divisa.from_dict(d) for d in data["results"]],
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
            status=data["status"], results=CotizacionFecha.from_dict(data["results"])
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
            status=data["status"],
            metadata=Metadata.from_dict(data["metadata"]),
            results=[CotizacionFecha.from_dict(d) for d in data["results"]],
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
        return cls(status=data["status"], error_messages=data["errorMessages"])
