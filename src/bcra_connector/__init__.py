from .__about__ import __version__
from .bcra_connector import BCRAApiError, BCRAConnector
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
from .estadisticas_cambiarias import Metadata, Resultset
from .principales_variables import DatosVariable, PrincipalesVariables
from .rate_limiter import RateLimitConfig
from .timeout_config import TimeoutConfig

__all__ = [
    "__version__",
    # Core
    "BCRAConnector",
    "BCRAApiError",
    "RateLimitConfig",
    "TimeoutConfig",
    # Principales Variables
    "PrincipalesVariables",
    "DatosVariable",
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
    "Resultset",
    "Metadata",
    "DivisaResponse",
    "CotizacionResponse",
    "CotizacionesResponse",
    "CambiariasErrorResponse",
]
