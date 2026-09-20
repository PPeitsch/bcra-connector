"""Per-domain clients exposed as attributes of :class:`~bcra_connector.BCRAConnector`."""

from .base import DomainClient
from .cheques import ChequesClient
from .deudores import DeudoresClient
from .monetarias import MonetariasClient

__all__ = ["DomainClient", "ChequesClient", "DeudoresClient", "MonetariasClient"]
