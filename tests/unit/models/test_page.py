"""Page[T]: the list-compatible return type with the API's own metadata."""

from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from bcra_connector.models import Page, resultset


@dataclass
class Row:
    value: int

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}


ROWS = [Row(1), Row(2), Row(3)]


class TestBehavesLikeAList:
    """Code written against the previous return type must keep working."""

    def test_iteration_length_and_indexing(self) -> None:
        page = Page(ROWS)
        assert [row.value for row in page] == [1, 2, 3]
        assert len(page) == 3
        assert page[0] is ROWS[0]
        assert page[-1] is ROWS[2]

    def test_slicing_returns_a_plain_list(self) -> None:
        page = Page(ROWS)
        assert page[1:] == ROWS[1:]
        assert isinstance(page[1:], list)

    def test_equals_the_list_it_replaces(self) -> None:
        assert Page(ROWS) == ROWS
        assert Page(ROWS) != ROWS[:2]
        assert Page(ROWS) == Page(ROWS)
        assert Page(ROWS, count=9) != Page(ROWS, count=3)

    def test_unrelated_types_are_not_equal(self) -> None:
        assert Page(ROWS) != "not a page"

    def test_empty_page_is_falsy_through_len(self) -> None:
        assert not Page([])
        assert Page(ROWS)


class TestMetadata:
    def test_defaults(self) -> None:
        page: Page[Row] = Page()
        assert page.results == []
        assert page.count is None
        assert page.offset == 0
        assert page.limit is None

    @pytest.mark.parametrize(
        "count,offset,rows,expected",
        [
            (10, 0, 3, True),  # 3 of 10 from the start
            (3, 0, 3, False),  # the whole thing
            (10, 7, 3, False),  # the tail
            (10, 8, 3, False),  # more than reported: never negative-ish
            (None, 0, 3, False),  # nothing reported: nothing to ask for
        ],
    )
    def test_has_more(self, count: int, offset: int, rows: int, expected: bool) -> None:
        page = Page(ROWS[:1] * rows, count=count, offset=offset)
        assert page.has_more is expected


class TestConversions:
    def test_to_dict_uses_the_rows_own_to_dict(self) -> None:
        assert Page(ROWS, count=3, limit=10).to_dict() == {
            "results": [{"value": 1}, {"value": 2}, {"value": 3}],
            "count": 3,
            "offset": 0,
            "limit": 10,
        }

    def test_to_dict_leaves_plain_rows_alone(self) -> None:
        assert Page([1, 2]).to_dict()["results"] == [1, 2]

    def test_to_dataframe_has_one_row_per_result(self) -> None:
        pytest.importorskip("pandas")
        df = Page(ROWS).to_dataframe()
        assert len(df) == 3
        assert list(df["value"]) == [1, 2, 3]

    def test_to_dataframe_without_pandas(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys

        monkeypatch.setitem(sys.modules, "pandas", None)
        with pytest.raises(ImportError, match=r"bcra-connector\[pandas\]"):
            Page(ROWS).to_dataframe()


class TestResultsetHelper:
    """`resultset()` keeps only what the endpoint actually reported."""

    @pytest.mark.parametrize(
        "data,expected",
        [
            ({}, {}),
            ({"metadata": None}, {}),
            ({"metadata": {}}, {}),
            ({"metadata": {"resultset": "nope"}}, {}),
            (
                {"metadata": {"resultset": {"count": 5, "offset": 1, "limit": 10}}},
                {"count": 5, "offset": 1, "limit": 10},
            ),
            ({"metadata": {"resultset": {"count": 5}}}, {"count": 5}),
            ({"metadata": {"resultset": {"count": "5", "limit": 10}}}, {"limit": 10}),
        ],
    )
    def test_extraction(self, data: Dict[str, Any], expected: Dict[str, Any]) -> None:
        assert resultset(data) == expected

    def test_page_built_from_a_response(self) -> None:
        data = {"metadata": {"resultset": {"count": 50, "offset": 10, "limit": 5}}}
        rows: List[Row] = ROWS[:2]
        page = Page(rows, **resultset(data))
        assert (page.count, page.offset, page.limit) == (50, 10, 5)
        assert page.has_more
