"""
Principales Variables Module.

This module provides data models and response handlers for the BCRA Monetary Statistics API (Principales Variables).
"""

from ..models import Metadata, Resultset, deprecated_exports
from .principales_variables import (
    DatosVariable,
    DetalleMonetaria,
    PrincipalesVariables,
)

# Deprecated until 1.0; imported through __getattr__ so that using one says so.
__getattr__ = deprecated_exports(
    "bcra_connector.principales_variables.principales_variables",
    DatosVariableResponse="use the Page returned by the corresponding connector method",
)

__all__ = [
    "DatosVariable",
    "DatosVariableResponse",
    "DetalleMonetaria",
    "Metadata",
    "PrincipalesVariables",
    "Resultset",
]
