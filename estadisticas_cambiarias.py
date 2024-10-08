from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import date


@dataclass
class Divisa:
    """
    Represents a currency.

    :param codigo: The currency code
    :param denominacion: The currency name
    """
    codigo: str
    denominacion: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Divisa':
        """Create a Divisa instance from a dictionary."""
        return cls(
            codigo=data['codigo'],
            denominacion=data['denominacion']
        )


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
    def from_dict(cls, data: Dict[str, Any]) -> 'CotizacionDetalle':
        """Create a CotizacionDetalle instance from a dictionary."""
        return cls(
            codigo_moneda=data['codigoMoneda'],
            descripcion=data['descripcion'],
            tipo_pase=float(data['tipoPase']),
            tipo_cotizacion=float(data['tipoCotizacion'])
        )


@dataclass
class CotizacionFecha:
    """
    Represents currency quotations for a specific date.

    :param fecha: The date of the quotations
    :param detalle: List of quotation details
    """
    fecha: date
    detalle: List[CotizacionDetalle]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CotizacionFecha':
        """Create a CotizacionFecha instance from a dictionary."""
        return cls(
            fecha=date.fromisoformat(data['fecha']),
            detalle=[CotizacionDetalle.from_dict(d) for d in data['detalle']]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the CotizacionFecha instance to a dictionary."""
        return {
            'fecha': self.fecha.isoformat(),
            'detalle': [
                {
                    'codigoMoneda': d.codigo_moneda,
                    'descripcion': d.descripcion,
                    'tipoPase': d.tipo_pase,
                    'tipoCotizacion': d.tipo_cotizacion
                } for d in self.detalle
            ]
        }
