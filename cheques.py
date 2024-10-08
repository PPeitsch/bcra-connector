from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import date


@dataclass
class Entidad:
    """
    Represents a financial entity.

    :param codigo_entidad: The entity's code
    :param denominacion: The entity's name
    """
    codigo_entidad: int
    denominacion: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entidad':
        """Create an Entidad instance from a dictionary."""
        return cls(
            codigo_entidad=data['codigoEntidad'],
            denominacion=data['denominacion']
        )


@dataclass
class ChequeDetalle:
    """
    Represents details of a reported check.

    :param sucursal: The branch number
    :param numero_cuenta: The account number
    :param causal: The reason for reporting
    """
    sucursal: int
    numero_cuenta: int
    causal: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChequeDetalle':
        """Create a ChequeDetalle instance from a dictionary."""
        return cls(
            sucursal=data['sucursal'],
            numero_cuenta=data['numeroCuenta'],
            causal=data['causal']
        )


@dataclass
class Cheque:
    """
    Represents a reported check.

    :param numero_cheque: The check number
    :param denunciado: Whether the check is reported
    :param fecha_procesamiento: The processing date
    :param denominacion_entidad: The name of the entity
    :param detalles: List of check details
    """
    numero_cheque: int
    denunciado: bool
    fecha_procesamiento: date
    denominacion_entidad: str
    detalles: List[ChequeDetalle]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cheque':
        """Create a Cheque instance from a dictionary."""
        return cls(
            numero_cheque=data['numeroCheque'],
            denunciado=data['denunciado'],
            fecha_procesamiento=date.fromisoformat(data['fechaProcesamiento']),
            denominacion_entidad=data['denominacionEntidad'],
            detalles=[ChequeDetalle.from_dict(d) for d in data.get('detalles', [])]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Cheque instance to a dictionary."""
        return {
            'numeroCheque': self.numero_cheque,
            'denunciado': self.denunciado,
            'fechaProcesamiento': self.fecha_procesamiento.isoformat(),
            'denominacionEntidad': self.denominacion_entidad,
            'detalles': [
                {
                    'sucursal': d.sucursal,
                    'numeroCuenta': d.numero_cuenta,
                    'causal': d.causal
                } for d in self.detalles
            ]
        }
