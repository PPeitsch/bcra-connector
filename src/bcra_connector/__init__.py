"""
BCRA Connector Package.

This package provides a Python client for interacting with the Central Bank of Argentina (BCRA) APIs.
It includes modules for retrieving:
- Principal Variables (Principales Variables)
- Checks (Cheques)
- Exchange Statistics (Estadísticas Cambiarias)
- Central de Deudores (Debtor Registry)
"""

from .__about__ import __version__
from .bcra_connector import BCRAApiError, BCRAConnector
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

# Import from principales_variables
from .principales_variables import (
    DatosVariable,
    DatosVariableResponse,
    DetalleMonetaria,
    PrincipalesVariables,
)
from .rate_limiter import RateLimitConfig
from .timeout_config import TimeoutConfig

__all__ = [
    "__version__",
    # Core
    "BCRAConnector",
    "BCRAApiError",
    "RateLimitConfig",
    "TimeoutConfig",
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
