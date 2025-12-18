"""
Central de Deudores API module.
Provides dataclasses for BCRA's Central de Deudores (Debtor Registry) API.
"""

from .central_deudores import (
    CausalCheques,
    ChequeRechazado,
    ChequesRechazados,
    Deudor,
    EntidadCheques,
    EntidadDeuda,
    Periodo,
)

__all__ = [
    "EntidadDeuda",
    "Periodo",
    "Deudor",
    "ChequeRechazado",
    "EntidadCheques",
    "CausalCheques",
    "ChequesRechazados",
]
