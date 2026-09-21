"""Resultset and Metadata are one pair of classes, not two (issue #138)."""

import pytest

import bcra_connector
from bcra_connector import Metadata, Resultset
from bcra_connector.estadisticas_cambiarias import Metadata as CambiariasMetadata
from bcra_connector.estadisticas_cambiarias import Resultset as CambiariasResultset
from bcra_connector.models import Metadata as ModelsMetadata
from bcra_connector.models import Resultset as ModelsResultset
from bcra_connector.principales_variables import Metadata as MonetariasMetadata
from bcra_connector.principales_variables import Resultset as MonetariasResultset

BLOCK = {"count": 100, "offset": 0, "limit": 50}


class TestOneClass:
    """Every import path lands on the same object."""

    @pytest.mark.parametrize(
        "alias",
        [ModelsResultset, MonetariasResultset, CambiariasResultset, Resultset],
    )
    def test_resultset_paths_agree(self, alias: type) -> None:
        assert alias is ModelsResultset

    @pytest.mark.parametrize(
        "alias",
        [ModelsMetadata, MonetariasMetadata, CambiariasMetadata, Metadata],
    )
    def test_metadata_paths_agree(self, alias: type) -> None:
        assert alias is ModelsMetadata

    def test_the_old_per_api_aliases_still_resolve(self) -> None:
        with pytest.warns(DeprecationWarning, match="use bcra_connector.Resultset"):
            assert bcra_connector.EstadisticasCambiariasResultset is Resultset
        with pytest.warns(DeprecationWarning, match="use bcra_connector.Metadata"):
            assert bcra_connector.EstadisticasCambiariasMetadata is Metadata

    def test_instances_compare_across_import_paths(self) -> None:
        assert MonetariasResultset.from_dict(BLOCK) == CambiariasResultset.from_dict(
            BLOCK
        )


class TestValidation:
    """The surviving behaviour is the validating one."""

    def test_round_trip(self) -> None:
        assert Resultset.from_dict(BLOCK).to_dict() == BLOCK

    @pytest.mark.parametrize(
        ("bad", "message"),
        [
            ({"count": "many", "offset": 0, "limit": 50}, "'count' must be int"),
            ({"count": 100, "offset": None, "limit": 50}, "'offset' must be int"),
            ({"count": 100, "offset": 0}, "'limit' is missing"),
        ],
    )
    def test_unreadable_fields_name_themselves(self, bad: dict, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            CambiariasResultset.from_dict(bad)

    def test_numeric_strings_are_read_as_numbers(self) -> None:
        """The helpers convert, as the other models always did."""
        assert CambiariasResultset.from_dict(
            {"count": "100", "offset": "0", "limit": "50"}
        ) == Resultset(count=100, offset=0, limit=50)

    def test_metadata_without_resultset_raises(self) -> None:
        with pytest.raises(ValueError, match="field 'resultset' is missing"):
            CambiariasMetadata.from_dict({})

    def test_metadata_parses_its_block(self) -> None:
        assert Metadata.from_dict({"resultset": BLOCK}).resultset == Resultset(
            count=100, offset=0, limit=50
        )
