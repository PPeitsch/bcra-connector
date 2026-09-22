"""
BCRA Connector Package.

This package provides a Python client for interacting with the Central Bank of Argentina (BCRA) APIs.
It includes modules for retrieving:
- Principal Variables (Principales Variables)
- Checks (Cheques)
- Exchange Statistics (Estadísticas Cambiarias)
- Central de Deudores (Debtor Registry)
"""

import logging

from .__about__ import __version__
from .bcra_connector import BCRAConnector
from .central_deudores import (
    CausalCheques,
    ChequeRechazado,
    ChequesRechazados,
    Deudor,
    EntidadCheques,
    EntidadDeuda,
    Periodo,
)
from .cheques import Cheque, ChequeDetalle, Entidad
from .estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha, Divisa
from .exceptions import (
    BCRAApiError,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from .models import DateLike, Metadata, Page, Resultset, to_dataframe

# Import from principales_variables
from .principales_variables import DatosVariable, DetalleMonetaria, PrincipalesVariables
from .rate_limiter import RateLimitConfig
from .timeout_config import TimeoutConfig

# Library logging convention: emit records, never configure output. Applications
# decide handlers and levels (see BCRAConnector's ``debug`` flag for an opt-in).
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "__version__",
    # Core
    "BCRAConnector",
    "BCRAApiError",
    "BCRANotFoundError",
    "BCRARateLimitError",
    "BCRAServerError",
    "RateLimitConfig",
    "TimeoutConfig",
    "DateLike",
    "Page",
    "to_dataframe",
    "Resultset",
    "Metadata",
    # Principales Variables / Monetarias v4.0
    "PrincipalesVariables",
    "DatosVariable",
    "DetalleMonetaria",
    # Cheques
    "Entidad",
    "ChequeDetalle",
    "Cheque",
    # Estadísticas Cambiarias
    "Divisa",
    "CotizacionDetalle",
    "CotizacionFecha",
    # Central de Deudores
    "EntidadDeuda",
    "Periodo",
    "Deudor",
    "ChequeRechazado",
    "EntidadCheques",
    "CausalCheques",
    "ChequesRechazados",
]
