"""Per-domain clients exposed as attributes of :class:`~bcra_connector.BCRAConnector`."""

from .base import DomainClient
from .cambiarias import CambiariasClient
from .cheques import ChequesClient
from .deudores import DeudoresClient
from .monetarias import MonetariasClient

__all__ = [
    "DomainClient",
    "CambiariasClient",
    "ChequesClient",
    "DeudoresClient",
    "MonetariasClient",
]
