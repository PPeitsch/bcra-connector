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
        "bad",
        [
            {"count": "100", "offset": 0, "limit": 50},
            {"count": 100, "offset": None, "limit": 50},
            {"count": 100, "offset": 0},
        ],
    )
    def test_non_integer_fields_raise(self, bad: dict) -> None:
        with pytest.raises(ValueError, match="Invalid types for Resultset fields"):
            CambiariasResultset.from_dict(bad)

    def test_metadata_without_resultset_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing or invalid 'resultset'"):
            CambiariasMetadata.from_dict({})

    def test_metadata_parses_its_block(self) -> None:
        assert Metadata.from_dict({"resultset": BLOCK}).resultset == Resultset(
            count=100, offset=0, limit=50
        )
