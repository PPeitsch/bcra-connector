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
import warnings
from importlib import import_module

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

# Superseded names, kept until 1.0. Reaching one warns and says what replaces it;
# the whole block goes away with the classes.
_PAGE = "use the Page returned by the corresponding connector method"
_ERROR = "every API error is raised as a BCRAApiError"
_SHARED = "use bcra_connector.{} instead"


def __getattr__(name: str) -> object:
    """Serve the deprecated names, warning once per access site."""
    sources = {
        "DatosVariableResponse": ("principales_variables", "DatosVariableResponse"),
        "EntidadResponse": ("cheques", "EntidadResponse"),
        "ChequeResponse": ("cheques", "ChequeResponse"),
        "ChequesErrorResponse": ("cheques", "ErrorResponse"),
        "DivisaResponse": ("estadisticas_cambiarias", "DivisaResponse"),
        "CotizacionResponse": ("estadisticas_cambiarias", "CotizacionResponse"),
        "CotizacionesResponse": ("estadisticas_cambiarias", "CotizacionesResponse"),
        "CambiariasErrorResponse": ("estadisticas_cambiarias", "ErrorResponse"),
    }
    if name in sources:
        package, attribute = sources[name]
        message = _ERROR if attribute == "ErrorResponse" else _PAGE
        warnings.warn(
            f"{name} is deprecated and will be removed in 1.0; {message}.",
            DeprecationWarning,
            stacklevel=2,
        )
        module = import_module(f".{package}.{package}", __name__)
        return getattr(module, attribute)
    shared = {
        "EstadisticasCambiariasResultset": ("Resultset", Resultset),
        "EstadisticasCambiariasMetadata": ("Metadata", Metadata),
    }
    if name in shared:
        canonical, value = shared[name]
        warnings.warn(
            f"{name} is deprecated and will be removed in 1.0; "
            f"{_SHARED.format(canonical)}.",
            DeprecationWarning,
            stacklevel=2,
        )
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
