"""
Estadísticas Cambiarias Module.

This module provides data models and response handlers for the BCRA Exchange Statistics API (Estadísticas Cambiarias).
"""

from ..models import Metadata, Resultset, deprecated_exports
from .estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha, Divisa

# Deprecated until 1.0; imported through __getattr__ so that using one says so.
__getattr__ = deprecated_exports(
    "bcra_connector.estadisticas_cambiarias.estadisticas_cambiarias",
    DivisaResponse="use the Page returned by the corresponding connector method",
    CotizacionResponse="use the Page returned by the corresponding connector method",
    CotizacionesResponse="use the Page returned by the corresponding connector method",
    ErrorResponse="every API error is raised as a BCRAApiError",
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
