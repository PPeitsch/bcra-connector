"""
Principales Variables Module.

This module provides data models and response handlers for the BCRA Monetary Statistics API (Principales Variables).
"""

from .principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    Metadata,
    PrincipalesVariables,
    Resultset,
)

__all__ = [
    "DatosVariable",
    "DatosVariableResponse",
    "DetalleMonetaria",
    "Metadata",
    "PrincipalesVariables",
    "Resultset",
]
