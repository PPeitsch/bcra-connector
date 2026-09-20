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
from .cheques import Cheque, ChequeDetalle, ChequeResponse, Entidad, EntidadResponse
from .cheques import ErrorResponse as ChequesErrorResponse
from .estadisticas_cambiarias import (
    CotizacionDetalle,
    CotizacionesResponse,
    CotizacionFecha,
    CotizacionResponse,
    Divisa,
    DivisaResponse,
)
from .estadisticas_cambiarias import ErrorResponse as CambiariasErrorResponse
from .estadisticas_cambiarias import Metadata as EstadisticasCambiariasMetadata
from .estadisticas_cambiarias import Resultset as EstadisticasCambiariasResultset
from .exceptions import (
    BCRAApiError,
    BCRANotFoundError,
    BCRARateLimitError,
    BCRAServerError,
)
from .models import Page

# Import from principales_variables
from .principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
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
    "Page",
    # Principales Variables / Monetarias v4.0
    "PrincipalesVariables",
    "DatosVariable",
    "DatosVariableResponse",
    "DetalleMonetaria",
    # Cheques
    "Entidad",
    "ChequeDetalle",
    "Cheque",
    "EntidadResponse",
    "ChequeResponse",
    "ChequesErrorResponse",
    # Estadísticas Cambiarias
    "Divisa",
    "CotizacionDetalle",
    "CotizacionFecha",
    "EstadisticasCambiariasResultset",
    "EstadisticasCambiariasMetadata",
    "DivisaResponse",
    "CotizacionResponse",
    "CotizacionesResponse",
    "CambiariasErrorResponse",
    # Central de Deudores
    "EntidadDeuda",
    "Periodo",
    "Deudor",
    "ChequeRechazado",
    "EntidadCheques",
    "CausalCheques",
    "ChequesRechazados",
]
