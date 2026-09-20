"""Cheques Denunciados v1.0."""

import unicodedata
from typing import List

from ..cheques import Cheque, Entidad
from ..exceptions import BCRAApiError
from .base import DomainClient


def _normalize_name(name: str) -> str:
    """Casefold, strip accents and collapse whitespace for name matching."""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


class ChequesClient(DomainClient):
    """Financial entities and reported checks (``connector.cheques``)."""

    def entities(self) -> List[Entidad]:
        """
        Fetch the list of all financial entities.

        :return: A list of Entidad objects.
        :raises BCRAApiError: If the API request fails.
        """
        self.logger.info("Fetching financial entities")
        entities = self._list("cheques/v1.0/entidades", Entidad.from_dict, "financial entities")
        self.logger.info(f"Successfully fetched {len(entities)} entities")
        return entities

    def reported(self, codigo_entidad: int, numero_cheque: int) -> Cheque:
        """
        Fetch information about a check, reported or not.

        The API answers a check that isn't reported with ``denunciado: false``; a 404
        means the entity code doesn't exist.

        :param codigo_entidad: The code of the financial entity.
        :param numero_cheque: The check number.
        :return: A Cheque object with the check's information.
        :raises BCRANotFoundError: If the entity code is unknown.
        :raises BCRAApiError: If the API request fails or returns unexpected data.
        """
        self.logger.info(
            f"Fetching information for check {numero_cheque} from entity {codigo_entidad}"
        )
        return self._object(
            f"cheques/v1.0/denunciados/{codigo_entidad}/{numero_cheque}",
            Cheque.from_dict,
            f"reported check {numero_cheque}",
        )

    def is_reported(self, entity_name: str, check_number: int) -> bool:
        """
        Check whether a check is reported as stolen or lost.

        The entity is matched by name, ignoring case and accents: an exact match
        wins; otherwise a single entity containing ``entity_name`` is used.

        :param entity_name: The name of the financial entity, or a unique part of it.
        :param check_number: The check number. Must be positive.
        :return: True if the check is reported, False otherwise.
        :raises ValueError: If no entity or several entities match, or check_number
            is invalid.
        :raises BCRANotFoundError: If the API doesn't know the entity (HTTP 404).
        :raises BCRAApiError: If the API request fails.
        """
        if check_number <= 0:
            raise ValueError("Check number must be positive.")
        try:
            entities = self._http.cached("entidades", self.entities)
        except Exception as e:
            self.logger.error(
                f"Could not get entities to check denounced status for '{entity_name}': {e}"
            )
            raise
        entity = self.find_entity(entities, entity_name)
        try:
            cheque = self.reported(entity.codigo_entidad, check_number)
        except BCRAApiError as e:
            self.logger.error(
                f"API error checking denounced status for check {check_number} "
                f"of entity '{entity_name}': {e}"
            )
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error checking denounced status for check {check_number} "
                f"of entity '{entity_name}': {e}"
            )
            raise BCRAApiError(
                f"Unexpected error during check verification for '{entity_name}', "
                f"check {check_number}: {e}"
            ) from e
        return cheque.denunciado

    @staticmethod
    def find_entity(entities: List[Entidad], entity_name: str) -> Entidad:
        """Resolve an entity by name: exact match first, then a unique substring."""
        query = _normalize_name(entity_name)
        named = [
            (e, _normalize_name(e.denominacion)) for e in entities if e.denominacion
        ]
        exact = [e for e, name in named if name == query]
        if exact:
            return exact[0]
        partial = [e for e, name in named if query and query in name]
        if len(partial) == 1:
            return partial[0]
        if not partial:
            raise ValueError(f"Entity '{entity_name}' not found")
        names = sorted(e.denominacion for e in partial)
        shown = 10
        candidates = ", ".join(names[:shown]) + (", ..." if len(names) > shown else "")
        raise ValueError(
            f"Entity '{entity_name}' matches {len(partial)} entities: {candidates}. "
            "Use a more specific name."
        )
