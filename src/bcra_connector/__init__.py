from ._version import __version__, version_info
from .bcra_connector import BCRAConnector, BCRAApiError
from .rate_limiter import RateLimitConfig
from .timeout_config import TimeoutConfig
from .principales_variables import (
    PrincipalesVariables,
    DatosVariable,
)
from .cheques import (
    Entidad,
    ChequeDetalle,
    Cheque,
    EntidadResponse,
    ChequeResponse,
    ErrorResponse as ChequesErrorResponse,
)
from .estadisticas_cambiarias import (
    Divisa,
    CotizacionDetalle,
    CotizacionFecha,
    Resultset,
    Metadata,
    DivisaResponse,
    CotizacionResponse,
    CotizacionesResponse,
    ErrorResponse as CambiariasErrorResponse,
)

__all__ = [
    "__version__",
    "version_info",
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
