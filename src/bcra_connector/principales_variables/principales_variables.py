"""
Data models for BCRA's Principal Variables API (Monetarias v4.0).
Defines classes for handling economic indicators, their historical data, and API responses.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import pandas as pd


# src/bcra_connector/principales_variables/principales_variables.py
@dataclass
class Resultset:
    """
    Represents metadata about the result set for Monetarias API v4.0 data.
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
    Represents metadata about the response for Monetarias API v4.0 data.
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
    Represents a principal variable or monetary series from the BCRA API (v4.0).

    :param idVariable: The ID of the variable/series.
    :param descripcion: The description of the variable/series.
    :param categoria: The category of the monetary series.
    :param tipoSerie: The type of series.
    :param periodicidad: The periodicity of the series.
    :param unidadExpresion: The unit of expression.
    :param moneda: The currency.
    :param primerFechaInformada: The first date reported.
    :param ultFechaInformada: The last date reported.
    :param ultValorInformado: The last value reported.
    """

    idVariable: int
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    tipoSerie: Optional[str] = None
    periodicidad: Optional[str] = None
    unidadExpresion: Optional[str] = None
    moneda: Optional[str] = None
    primerFechaInformada: Optional[date] = None
    ultFechaInformada: Optional[date] = None
    ultValorInformado: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrincipalesVariables":
        """Create a PrincipalesVariables instance from a dictionary (v4.0 format)."""
        try:
            # Parse optional date fields
            primer_fecha = None
            if data.get("primerFechaInformada"):
                primer_fecha = date.fromisoformat(str(data["primerFechaInformada"]))

            ult_fecha = None
            if data.get("ultFechaInformada"):
                ult_fecha = date.fromisoformat(str(data["ultFechaInformada"]))

            # Parse optional float field
            ult_valor = None
            if data.get("ultValorInformado") is not None:
                ult_valor = float(data["ultValorInformado"])

            return cls(
                idVariable=int(data["idVariable"]),
                descripcion=data.get("descripcion"),
                categoria=data.get("categoria"),
                tipoSerie=data.get("tipoSerie"),
                periodicidad=data.get("periodicidad"),
                unidadExpresion=data.get("unidadExpresion"),
                moneda=data.get("moneda"),
                primerFechaInformada=primer_fecha,
                ultFechaInformada=ult_fecha,
                ultValorInformado=ult_valor,
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
        """Convert the PrincipalesVariables instance to a dictionary (v4.0 format)."""
        result: Dict[str, Any] = {
            "idVariable": self.idVariable,
        }
        if self.descripcion is not None:
            result["descripcion"] = self.descripcion
        if self.categoria is not None:
            result["categoria"] = self.categoria
        if self.tipoSerie is not None:
            result["tipoSerie"] = self.tipoSerie
        if self.periodicidad is not None:
            result["periodicidad"] = self.periodicidad
        if self.unidadExpresion is not None:
            result["unidadExpresion"] = self.unidadExpresion
        if self.moneda is not None:
            result["moneda"] = self.moneda
        if self.primerFechaInformada is not None:
            result["primerFechaInformada"] = self.primerFechaInformada.isoformat()
        if self.ultFechaInformada is not None:
            result["ultFechaInformada"] = self.ultFechaInformada.isoformat()
        if self.ultValorInformado is not None:
            result["ultValorInformado"] = self.ultValorInformado
        return result

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the PrincipalesVariables instance to a pandas DataFrame.

        Requires pandas to be installed: ``pip install bcra-connector[pandas]``

        :return: A single-row DataFrame with all variable attributes.
        :raises ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install bcra-connector[pandas]"
            )
        return pd.DataFrame([self.to_dict()])


@dataclass
class DetalleMonetaria:
    """
    Represents a single data point in the historical data for a variable/series (v4.0).

    :param fecha: The date of the data point.
    :param valor: The value of the variable/series on the given date.
    """

    fecha: date
    valor: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetalleMonetaria":
        """Create a DetalleMonetaria instance from a dictionary."""
        try:
            return cls(
                fecha=date.fromisoformat(str(data["fecha"])),
                valor=float(data["valor"]),
            )
        except KeyError as e:
            raise ValueError(f"Missing key in DetalleMonetaria data: {e}") from e
        except ValueError as e:
            raise ValueError(
                f"Invalid data type or format in DetalleMonetaria data: {e}"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DetalleMonetaria instance to a dictionary."""
        return {
            "fecha": self.fecha.isoformat(),
            "valor": self.valor,
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the DetalleMonetaria instance to a pandas DataFrame.

        Requires pandas: ``pip install bcra-connector[pandas]``

        :return: A single-row DataFrame with fecha and valor.
        :raises ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install bcra-connector[pandas]"
            )
        return pd.DataFrame([self.to_dict()])


@dataclass
class DatosVariable:
    """
    Represents historical data for a variable/series (v4.0 structure).

    :param idVariable: The ID of the variable/series.
    :param detalle: List of DetalleMonetaria objects with historical data points.
    """

    idVariable: int
    detalle: List[DetalleMonetaria]

    def __post_init__(self) -> None:
        """Validate instance after initialization."""
        if not isinstance(self.idVariable, int) or self.idVariable < 0:
            raise ValueError("Variable ID must be a non-negative integer")
        if not isinstance(self.detalle, list):
            raise ValueError("Detalle must be a list")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatosVariable":
        """Create a DatosVariable instance from a dictionary."""
        try:
            detalle_list = []
            if data.get("detalle"):
                detalle_list = [
                    DetalleMonetaria.from_dict(item) for item in data["detalle"]
                ]

            return cls(
                idVariable=int(data["idVariable"]),
                detalle=detalle_list,
            )
        except KeyError as e:
            raise ValueError(f"Missing key in DatosVariable data: {e}") from e
        except ValueError as e:
            raise ValueError(
                f"Invalid data type or format in DatosVariable data: {e}"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DatosVariable instance to a dictionary."""
        return {
            "idVariable": self.idVariable,
            "detalle": [item.to_dict() for item in self.detalle],
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the historical data to a pandas DataFrame.

        Returns a DataFrame with columns: idVariable, fecha, valor.
        Each row represents one data point from the detalle list.

        Requires pandas: ``pip install bcra-connector[pandas]``

        :return: DataFrame with all historical data points.
        :raises ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install with: pip install bcra-connector[pandas]"
            )
        rows = [
            {"idVariable": self.idVariable, "fecha": d.fecha, "valor": d.valor}
            for d in self.detalle
        ]
        return pd.DataFrame(rows)

    def __eq__(self, other: object) -> bool:
        """Compare DatosVariable instances based on idVariable."""
        if not isinstance(other, DatosVariable):
            return NotImplemented
        return self.idVariable == other.idVariable


@dataclass
class DatosVariableResponse:
    """
    Represents the full response for fetching historical data for a variable/series (v4.0).

    :param status: HTTP status code.
    :param metadata: Metadata object containing count, offset, and limit.
    :param results: List of DatosVariable objects.
    """

    status: int
    metadata: Metadata
    results: List[DatosVariable]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatosVariableResponse":
        """Create a DatosVariableResponse instance from a dictionary."""
        if "status" not in data:
            raise ValueError("Missing 'status' in DatosVariableResponse data")
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

        return cls(
            status=int(data["status"]), metadata=metadata_obj, results=results_list
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DatosVariableResponse instance to a dictionary."""
        return {
            "status": self.status,
            "metadata": (
                self.metadata.resultset.to_dict()
                if self.metadata and self.metadata.resultset
                else None
            ),
            "results": [item.to_dict() for item in self.results],
        }
