"""Per-domain clients exposed as attributes of :class:`~bcra_connector.BCRAConnector`."""

from .base import DomainClient
from .deudores import DeudoresClient

__all__ = ["DomainClient", "DeudoresClient"]
