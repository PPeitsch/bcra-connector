"""
Data models for BCRA's Principal Variables API (Monetarias v4.0).
Defines classes for handling economic indicators, their historical data, and API responses.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import (
    Metadata,
    install_legacy_names,
    optional,
    require,
    to_dataframe,
)

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class PrincipalesVariables:
    """
    Represents a principal variable or monetary series from the BCRA API (v4.0).

    The API's own camelCase names (``idVariable``, ``ultValorInformado``, ...)
    still work, with a ``DeprecationWarning``, until 1.0.

    :param id_variable: The ID of the variable/series.
    :param descripcion: The description of the variable/series.
    :param categoria: The category of the monetary series.
    :param tipo_serie: The type of series.
    :param periodicidad: The periodicity of the series.
    :param unidad_expresion: The unit of expression.
    :param moneda: The currency.
    :param primer_fecha_informada: The first date reported.
    :param ult_fecha_informada: The last date reported.
    :param ult_valor_informado: The last value reported.
    """

    id_variable: int
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    tipo_serie: Optional[str] = None
    periodicidad: Optional[str] = None
    unidad_expresion: Optional[str] = None
    moneda: Optional[str] = None
    primer_fecha_informada: Optional[date] = None
    ult_fecha_informada: Optional[date] = None
    ult_valor_informado: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrincipalesVariables":
        """Create a PrincipalesVariables instance from a dictionary (v4.0 format)."""
        return cls(
            id_variable=require(data, "idVariable", int),
            descripcion=optional(data, "descripcion", str),
            categoria=optional(data, "categoria", str),
            tipo_serie=optional(data, "tipoSerie", str),
            periodicidad=optional(data, "periodicidad", str),
            unidad_expresion=optional(data, "unidadExpresion", str),
            moneda=optional(data, "moneda", str),
            primer_fecha_informada=optional(data, "primerFechaInformada", date),
            ult_fecha_informada=optional(data, "ultFechaInformada", date),
            ult_valor_informado=optional(data, "ultValorInformado", float),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the PrincipalesVariables instance to a dictionary (v4.0 format)."""
        result: Dict[str, Any] = {
            "idVariable": self.id_variable,
        }
        if self.descripcion is not None:
            result["descripcion"] = self.descripcion
        if self.categoria is not None:
            result["categoria"] = self.categoria
        if self.tipo_serie is not None:
            result["tipoSerie"] = self.tipo_serie
        if self.periodicidad is not None:
            result["periodicidad"] = self.periodicidad
        if self.unidad_expresion is not None:
            result["unidadExpresion"] = self.unidad_expresion
        if self.moneda is not None:
            result["moneda"] = self.moneda
        if self.primer_fecha_informada is not None:
            result["primerFechaInformada"] = self.primer_fecha_informada.isoformat()
        if self.ult_fecha_informada is not None:
            result["ultFechaInformada"] = self.ult_fecha_informada.isoformat()
        if self.ult_valor_informado is not None:
            result["ultValorInformado"] = self.ult_valor_informado
        return result

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the PrincipalesVariables instance to a pandas DataFrame.

        Requires pandas to be installed: ``pip install bcra-connector[pandas]``

        :return: A single-row DataFrame with all variable attributes.
        :raises ImportError: If pandas is not installed.
        """
        return to_dataframe([self])


# The API's own camelCase names, until 1.0.
install_legacy_names(
    PrincipalesVariables,
    idVariable="id_variable",
    tipoSerie="tipo_serie",
    unidadExpresion="unidad_expresion",
    primerFechaInformada="primer_fecha_informada",
    ultFechaInformada="ult_fecha_informada",
    ultValorInformado="ult_valor_informado",
)


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
        return cls(
            fecha=require(data, "fecha", date),
            valor=require(data, "valor", float),
        )

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
        return to_dataframe([self])


@dataclass
class DatosVariable:
    """
    Represents historical data for a variable/series (v4.0 structure).

    The API's own ``idVariable`` still works, with a ``DeprecationWarning``,
    until 1.0.

    :param id_variable: The ID of the variable/series.
    :param detalle: List of DetalleMonetaria objects with historical data points.
    """

    id_variable: int
    detalle: List[DetalleMonetaria]

    def __post_init__(self) -> None:
        """Validate instance after initialization."""
        if not isinstance(self.id_variable, int) or self.id_variable < 0:
            raise ValueError("Variable ID must be a non-negative integer")
        if not isinstance(self.detalle, list):
            raise ValueError("Detalle must be a list")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatosVariable":
        """Create a DatosVariable instance from a dictionary."""
        return cls(
            id_variable=require(data, "idVariable", int),
            detalle=[
                DetalleMonetaria.from_dict(item)
                for item in optional(data, "detalle", list, default=[])
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DatosVariable instance to a dictionary."""
        return {
            "idVariable": self.id_variable,
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
        rows = [
            {"idVariable": self.id_variable, "fecha": d.fecha, "valor": d.valor}
            for d in self.detalle
        ]
        return to_dataframe(rows)


install_legacy_names(DatosVariable, idVariable="id_variable")


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
        return cls(
            status=require(data, "status", int),
            metadata=Metadata.from_dict(require(data, "metadata", dict)),
            results=[
                DatosVariable.from_dict(item) for item in require(data, "results", list)
            ],
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
