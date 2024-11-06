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


@dataclass
class EntidadResponse:
    """
    Represents the response for the Entidades endpoint.

    :param status: The HTTP status code
    :param results: List of Entidad objects
    """
    status: int
    results: List[Entidad]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntidadResponse':
        """Create an EntidadResponse instance from a dictionary."""
        return cls(
            status=data['status'],
            results=[Entidad.from_dict(e) for e in data['results']]
        )


@dataclass
class ChequeResponse:
    """
    Represents the response for the Cheques Denunciados endpoint.

    :param status: The HTTP status code
    :param results: A Cheque object
    """
    status: int
    results: Cheque

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChequeResponse':
        """Create a ChequeResponse instance from a dictionary."""
        return cls(
            status=data['status'],
            results=Cheque.from_dict(data['results'])
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorResponse':
        """Create an ErrorResponse instance from a dictionary."""
        return cls(
            status=data['status'],
            error_messages=data['errorMessages']
        )