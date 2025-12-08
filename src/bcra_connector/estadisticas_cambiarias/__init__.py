"""
Estadísticas Cambiarias Module.

This module provides data models and response handlers for the BCRA Exchange Statistics API (Estadísticas Cambiarias).
"""

from .estadisticas_cambiarias import (
    CotizacionDetalle,
    CotizacionesResponse,
    CotizacionFecha,
    CotizacionResponse,
    Divisa,
    DivisaResponse,
    ErrorResponse,
    Metadata,
    Resultset,
)

__all__ = [
    "Divisa",
    "CotizacionDetalle",
    "CotizacionFecha",
    "Resultset",
    "Metadata",
    "DivisaResponse",
    "CotizacionResponse",
    "CotizacionesResponse",
    "ErrorResponse",
]
