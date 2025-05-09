"""
Data models for BCRA's Principal Variables API (Monetarias v3.0).
Defines classes for handling economic indicators, their historical data, and API responses.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List


# src/bcra_connector/principales_variables/principales_variables.py
@dataclass
class Resultset:
    """
    Represents metadata about the result set for Monetarias API v3.0 data.
    """

    count: int
    offset: int
    limit: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resultset":
        """Create a Resultset instance from a dictionary."""
        if (
            not isinstance(data.get("count"), int)
            or not isinstance(data.get("offset"), int)
            or not isinstance(data.get("limit"), int)
        ):
            raise ValueError("Invalid types for Resultset fields")
        return cls(count=data["count"], offset=data["offset"], limit=data["limit"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Resultset instance to a dictionary."""
        return {
            "count": self.count,
            "offset": self.offset,
            "limit": self.limit,
        }


@dataclass
class Metadata:
    """
    Represents metadata about the response for Monetarias API v3.0 data.
    """

    resultset: Resultset

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create a Metadata instance from a dictionary."""
        if "resultset" not in data or not isinstance(data["resultset"], dict):
            raise ValueError("Missing or invalid 'resultset' in Metadata")
        return cls(resultset=Resultset.from_dict(data["resultset"]))


@dataclass
class PrincipalesVariables:
    """
    Represents a principal variable or monetary series from the BCRA API (v3.0).

    :param idVariable: The ID of the variable/series.
    :param descripcion: The description of the variable/series.
    :param fecha: The date of the variable's/series' value.
    :param valor: The value of the variable/series.
    :param categoria: The category of the monetary series (e.g., "Principales Variables").
    """

    idVariable: int
    descripcion: str
    fecha: date
    valor: float
    categoria: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrincipalesVariables":
        """Create a PrincipalesVariables instance from a dictionary (v3.0 format)."""
        try:
            return cls(
                idVariable=int(data["idVariable"]),
                descripcion=str(data["descripcion"]),
                fecha=date.fromisoformat(str(data["fecha"])),
                valor=float(data["valor"]),
                categoria=str(data["categoria"]),
            )
        except KeyError as e:
            raise ValueError(f"Missing key in PrincipalesVariables data: {e}") from e
        except (
            ValueError
        ) as e:  # Catch float/int conversion errors or date format errors
            raise ValueError(
                f"Invalid data type or format in PrincipalesVariables data: {e}"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert the PrincipalesVariables instance to a dictionary (v3.0 format)."""
        return {
            "idVariable": self.idVariable,
            "descripcion": self.descripcion,
            "fecha": self.fecha.isoformat(),
            "valor": self.valor,
            "categoria": self.categoria,
        }


@dataclass
class DatosVariable:
    """
    Represents historical data for a variable/series (structure unchanged in v3.0 data points).

    :param idVariable: The ID of the variable/series.
    :param fecha: The date of the data point.
    :param valor: The value of the variable/series on the given date.
    """

    idVariable: int
    fecha: date
    valor: float

    def __post_init__(self) -> None:
        """Validate instance after initialization."""
        if not isinstance(self.idVariable, int) or self.idVariable < 0:
            raise ValueError("Variable ID must be a non-negative integer")
        if not isinstance(self.fecha, date):
            raise ValueError("Fecha must be a date object")
        # For valor, just validate it's a number but don't try to convert
        if not isinstance(self.valor, (int, float)):
            raise ValueError(f"Valor must be a number, got {type(self.valor).__name__}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatosVariable":
        """Create a DatosVariable instance from a dictionary."""
        try:
            instance = cls(
                idVariable=int(data["idVariable"]),
                fecha=date.fromisoformat(str(data["fecha"])),
                valor=float(data["valor"]),
            )
            return instance
        except KeyError as e:
            raise ValueError(f"Missing key in DatosVariable data: {e}") from e
        except (
            ValueError
        ) as e:  # Catch float/int conversion errors or date format errors
            raise ValueError(
                f"Invalid data type or format in DatosVariable data: {e}"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DatosVariable instance to a dictionary."""
        return {
            "idVariable": self.idVariable,
            "fecha": self.fecha.isoformat(),
            "valor": self.valor,
        }

    def __eq__(self, other: object) -> bool:
        """Compare DatosVariable instances based only on idVariable and fecha."""
        if not isinstance(other, DatosVariable):
            return NotImplemented
        return self.idVariable == other.idVariable and self.fecha == other.fecha


@dataclass
class DatosVariableResponse:
    """
    Represents the full response for fetching historical data for a variable/series (v3.0).

    :param metadata: Metadata object containing count, offset, and limit.
    :param results: List of DatosVariable objects.
    """

    metadata: Metadata
    results: List[DatosVariable]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatosVariableResponse":
        """Create a DatosVariableResponse instance from a dictionary."""
        if "metadata" not in data or not isinstance(data.get("metadata"), dict):
            raise ValueError(
                "Missing or invalid 'metadata' in DatosVariableResponse data"
            )
        if "results" not in data or not isinstance(data.get("results"), list):
            raise ValueError(
                "Missing or invalid 'results' in DatosVariableResponse data"
            )

        try:
            metadata_obj = Metadata.from_dict(data["metadata"])
            results_list = [DatosVariable.from_dict(item) for item in data["results"]]
        except ValueError as e:  # Catch errors from child model parsing
            raise ValueError(
                f"Error parsing components of DatosVariableResponse: {e}"
            ) from e

        return cls(metadata=metadata_obj, results=results_list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DatosVariableResponse instance to a dictionary."""
        return {
            "metadata": (
                self.metadata.resultset.to_dict()
                if self.metadata and self.metadata.resultset
                else None
            ),  # Assuming Resultset has to_dict
            "results": [item.to_dict() for item in self.results],
        }
