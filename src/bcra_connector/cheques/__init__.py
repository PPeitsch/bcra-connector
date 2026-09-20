"""
Cheques Module.

This module provides data models and response handlers for the BCRA Checks API.
"""

from ..models import deprecated_exports
from .cheques import Cheque, ChequeDetalle, Entidad

# Deprecated until 1.0; imported through __getattr__ so that using one says so.
__getattr__ = deprecated_exports(
    "bcra_connector.cheques.cheques",
    EntidadResponse="use the Page returned by the corresponding connector method",
    ChequeResponse="use the Page returned by the corresponding connector method",
    ErrorResponse="every API error is raised as a BCRAApiError",
)

__all__ = [
    "Entidad",
    "ChequeDetalle",
    "Cheque",
    "EntidadResponse",
    "ChequeResponse",
    "ErrorResponse",
]
