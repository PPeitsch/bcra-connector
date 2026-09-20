"""Central de Deudores v1.0."""

from ..central_deudores import ChequesRechazados, Deudor
from .base import DomainClient, identificacion


class DeudoresClient(DomainClient):
    """Debts and rejected checks by CUIT/CUIL/CDI (``connector.deudores``)."""

    def debts(self, cuit: str) -> Deudor:
        """
        Fetch current debts for a CUIT/CUIL/CDI.

        :param cuit: The CUIT/CUIL/CDI (11 digits, dashes allowed) to query.
        :return: A Deudor object with current debt information.
        :raises ValueError: If the identifier is not 11 digits.
        :raises BCRANotFoundError: If the registry has no data for it.
        :raises BCRAApiError: If the API request fails.
        """
        cuit = identificacion(cuit)
        self.logger.info("Fetching current debts from Central de Deudores")
        deudor = self._object(
            f"CentralDeDeudores/v1.0/Deudas/{cuit}", Deudor.from_dict, "deudas"
        )
        self.logger.info(f"Successfully fetched debts ({len(deudor.periodos)} periods)")
        return deudor

    def historical(self, cuit: str) -> Deudor:
        """
        Fetch historical debts (24 months) for a CUIT/CUIL/CDI.

        :param cuit: The CUIT/CUIL/CDI (11 digits, dashes allowed) to query.
        :return: A Deudor object with historical debt information.
        :raises ValueError: If the identifier is not 11 digits.
        :raises BCRANotFoundError: If the registry has no data for it.
        :raises BCRAApiError: If the API request fails.
        """
        cuit = identificacion(cuit)
        self.logger.info("Fetching historical debts from Central de Deudores")
        deudor = self._object(
            f"CentralDeDeudores/v1.0/Deudas/Historicas/{cuit}",
            Deudor.from_dict,
            "deudas historicas",
        )
        self.logger.info(
            f"Successfully fetched historical debts ({len(deudor.periodos)} periods)"
        )
        return deudor

    def rejected_checks(self, cuit: str) -> ChequesRechazados:
        """
        Fetch rejected checks for a CUIT/CUIL/CDI.

        :param cuit: The CUIT/CUIL/CDI (11 digits, dashes allowed) to query.
        :return: A ChequesRechazados object with rejected check details.
        :raises ValueError: If the identifier is not 11 digits.
        :raises BCRANotFoundError: If the registry has no data for it.
        :raises BCRAApiError: If the API request fails.
        """
        cuit = identificacion(cuit)
        self.logger.info("Fetching rejected checks from Central de Deudores")
        cheques = self._object(
            f"CentralDeDeudores/v1.0/Deudas/ChequesRechazados/{cuit}",
            ChequesRechazados.from_dict,
            "cheques rechazados",
        )
        total = sum(len(e.detalle) for c in cheques.causales for e in c.entidades)
        self.logger.info(f"Successfully fetched {total} rejected checks")
        return cheques
