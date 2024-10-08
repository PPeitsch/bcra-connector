from dataclasses import dataclass
from typing import Dict, Any
from datetime import date


@dataclass
class PrincipalesVariables:
    """
    Represents a principal variable from the BCRA API.

    :param idVariable: The ID of the variable
    :param cdSerie: The series code of the variable
    :param descripcion: The description of the variable
    :param fecha: The date of the variable's value
    :param valor: The value of the variable
    """
    idVariable: int
    cdSerie: int
    descripcion: str
    fecha: date
    valor: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrincipalesVariables':
        """Create a PrincipalesVariables instance from a dictionary."""
        return cls(
            idVariable=data['idVariable'],
            cdSerie=data['cdSerie'],
            descripcion=data['descripcion'],
            fecha=date.fromisoformat(data['fecha']),
            valor=float(data['valor'])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the PrincipalesVariables instance to a dictionary."""
        return {
            'idVariable': self.idVariable,
            'cdSerie': self.cdSerie,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat(),
            'valor': self.valor
        }


@dataclass
class DatosVariable:
    """
    Represents historical data for a variable.

    :param idVariable: The ID of the variable
    :param fecha: The date of the data point
    :param valor: The value of the variable on the given date
    """
    idVariable: int
    fecha: date
    valor: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatosVariable':
        """Create a DatosVariable instance from a dictionary."""
        return cls(
            idVariable=data['idVariable'],
            fecha=date.fromisoformat(data['fecha']),
            valor=float(data['valor'])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DatosVariable instance to a dictionary."""
        return {
            'idVariable': self.idVariable,
            'fecha': self.fecha.isoformat(),
            'valor': self.valor
        }
