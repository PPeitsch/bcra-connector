"""Types shared by every domain client."""

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
    overload,
)

if TYPE_CHECKING:
    import pandas as pd

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """A page of results plus the metadata the API reported about it.

    It behaves like the list it replaces — ``for row in page``, ``len(page)``,
    ``page[0]``, slicing and ``==`` against a list all work — so code written
    against the previous return type keeps running, while ``count``, ``offset``,
    ``limit`` and :attr:`has_more` become available.

    It deliberately does not subclass ``Sequence``: ``count`` is a number here,
    the one the API reports, not ``Sequence.count()``.

    ``count`` is what the endpoint reported as the total number of results, which
    is not always the length of this page: helpers that page through the whole
    range return every row with the total alongside. It is ``None`` when the
    endpoint reports nothing usable.
    """

    results: List[T] = field(default_factory=list)
    count: Optional[int] = None
    offset: int = 0
    limit: Optional[int] = None

    @property
    def has_more(self) -> bool:
        """Whether the endpoint has results past this page.

        ``False`` when the total is unknown: nothing was reported, so there is
        nothing to ask for.
        """
        if self.count is None:
            return False
        return self.offset + len(self.results) < self.count

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self) -> Iterator[T]:
        return iter(self.results)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> List[T]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[T, List[T]]:
        return self.results[index]

    def __eq__(self, other: object) -> bool:
        """Equal to another page with the same rows, or to a plain list of them."""
        if isinstance(other, Page):
            return (
                self.results == other.results
                and self.count == other.count
                and self.offset == other.offset
                and self.limit == other.limit
            )
        if isinstance(other, list):
            return self.results == other
        return NotImplemented

    def to_dict(self) -> Dict[str, Any]:
        """The page as a dictionary, rows included when they know how."""
        return {
            "results": [
                row.to_dict() if hasattr(row, "to_dict") else row
                for row in self.results
            ],
            "count": self.count,
            "offset": self.offset,
            "limit": self.limit,
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """Build a DataFrame with one row per result.

        :raises ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                'Install it with: pip install "bcra-connector[pandas]"'
            ) from e
        return pd.DataFrame(
            [row.to_dict() if hasattr(row, "to_dict") else row for row in self.results]
        )


def resultset(data: Dict[str, Any]) -> Dict[str, Any]:
    """Pull ``count``/``offset``/``limit`` out of a response's metadata.

    Every BCRA endpoint that paginates reports them under
    ``metadata.resultset``, but not all of them report all three, and some
    report none at all. Missing or non-integer values are dropped, so the
    :class:`Page` defaults apply.
    """
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    block = metadata.get("resultset")
    if not isinstance(block, dict):
        return {}
    return {
        key: block[key]
        for key in ("count", "offset", "limit")
        if isinstance(block.get(key), int)
    }
