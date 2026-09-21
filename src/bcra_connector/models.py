"""Types shared by every domain client."""

import warnings
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib import import_module
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
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

#: What every date input of the public API accepts: a ``date``, a ``datetime``
#: or an ISO 8601 string.
DateLike = Union[date, datetime, str]


def as_date(value: DateLike, param: str) -> date:
    """Normalize any accepted date input to a plain :class:`datetime.date`.

    Every endpoint of the BCRA API takes dates as ``YYYY-MM-DD`` and returns
    them with no time attached, so a ``datetime`` is reduced to its date and an
    ISO string is parsed rather than passed through: an unparseable one fails
    here, naming the parameter, instead of becoming an opaque API error.

    :param value: A ``date``, a ``datetime`` or an ISO 8601 string.
    :param param: The parameter name, used in the error message.
    :raises TypeError: If the value is of any other type.
    :raises ValueError: If the string is not an ISO 8601 date.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.strip()).date()
        except ValueError:
            raise ValueError(
                f"'{param}' must be an ISO 8601 date (YYYY-MM-DD), got {value!r}"
            ) from None
    raise TypeError(
        f"'{param}' must be a date, a datetime or an ISO 8601 string, "
        f"got {type(value).__name__}"
    )


_MISSING = object()


def require(data: Dict[str, Any], key: str, kind: type) -> Any:
    """Read one field of an API response, converted and checked.

    The single way every ``from_dict`` reads the payload, so that a malformed
    response fails the same way wherever it came from, naming the field and what
    was expected instead of raising a bare ``KeyError('codigoEntidad')`` or an
    ``invalid literal for int()`` that never says which field it was.

    ``kind`` is the type wanted: ``int``, ``float`` and ``bool`` convert,
    :class:`datetime.date` goes through :func:`as_date`, ``str`` converts
    anything scalar, and ``list``/``dict`` are checked without converting. Every
    failure is a ``ValueError``, whatever the field's type.

    The endpoint is not named here on purpose: the domain clients already wrap a
    parse failure into a :class:`BCRAApiError` that says which endpoint was being
    read, and the two messages compose.

    :raises ValueError: If the field is missing, or cannot be read as ``kind``.
    """
    value = data.get(key, _MISSING)
    if value is _MISSING:
        raise ValueError(f"field {key!r} is missing")
    return _convert(value, key, kind)


def optional(data: Dict[str, Any], key: str, kind: type, default: Any = None) -> Any:
    """Read a field that the API may omit or report as null.

    Same conversion and the same errors as :func:`require`; a missing or ``None``
    value yields ``default`` instead of failing.

    :raises ValueError: If the field is present and cannot be read as ``kind``.
    """
    value = data.get(key)
    if value is None:
        return default
    return _convert(value, key, kind)


def _convert(value: Any, key: str, kind: type) -> Any:
    """Convert one already-present value, or say what was expected."""
    if kind is date:
        try:
            return as_date(value, key)
        except TypeError as e:
            # One failure mode for the helpers: as_date rejects a wrong type with
            # TypeError, but every caller here only knows about ValueError.
            raise ValueError(str(e)) from e
    if kind in (list, dict):
        if not isinstance(value, kind):
            raise ValueError(
                f"field {key!r} must be {'a list' if kind is list else 'an object'}, "
                f"got {type(value).__name__}"
            )
        return value
    if kind is bool:
        return bool(value)
    if kind is str:
        if isinstance(value, (list, dict)):
            raise ValueError(
                f"field {key!r} must be a string, got {type(value).__name__}"
            )
        return value if isinstance(value, str) else str(value)
    try:
        return kind(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"field {key!r} must be {kind.__name__}, got {value!r}") from e


@dataclass
class Resultset:
    """The ``metadata.resultset`` block every paginated endpoint reports.

    Kept for the deprecated ``*Response`` models; :class:`Page` carries the same
    three numbers as plain attributes.
    """

    count: int
    offset: int
    limit: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resultset":
        """Create a Resultset instance from a dictionary."""
        return cls(
            count=require(data, "count", int),
            offset=require(data, "offset", int),
            limit=require(data, "limit", int),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Resultset instance to a dictionary."""
        return {
            "count": self.count,
            "offset": self.offset,
            "limit": self.limit,
        }


@dataclass
class Metadata:
    """The ``metadata`` block of a response, wrapping a :class:`Resultset`."""

    resultset: Resultset

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create a Metadata instance from a dictionary."""
        return cls(resultset=Resultset.from_dict(require(data, "resultset", dict)))


def deprecated_exports(source: str, **replacements: str) -> Callable[[str], Any]:
    """Build a module ``__getattr__`` that warns for names on their way out.

    Takes the module the names really live in and ``Name="what to use instead"``
    pairs, and returns a `PEP 562 <https://peps.python.org/pep-0562/>`_
    ``__getattr__``: the name still imports and works, but doing so says so.

    The names must not also be imported statically by the module installing
    this, or the warning never fires. Code inside the library imports them from
    their defining module, which is not deprecated — only the public export is.
    """

    def __getattr__(name: str) -> Any:
        replacement = replacements.get(name)
        if replacement is None:
            raise AttributeError(f"cannot import name {name!r} from {source!r}")
        warnings.warn(
            f"{name} is deprecated and will be removed in 1.0; {replacement}.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(import_module(source), name)

    return __getattr__


def install_legacy_names(cls: type, **aliases: str) -> None:
    """Keep a model's pre-1.0 field names working, with a ``DeprecationWarning``.

    Called right after the class body with ``oldName="new_name"`` pairs, it makes
    each old name readable as an attribute and accepted as a keyword argument,
    both warning and both removed in 1.0 — when the call goes away with its
    arguments.

    Only the names listed here are aliased: anything else still raises
    ``AttributeError`` or ``TypeError`` as usual, so a typo stays a typo.
    """

    def warn(old: str, new: str) -> None:
        warnings.warn(
            f"{cls.__name__}.{old} is deprecated and will be removed in 1.0; "
            f"use .{new} instead.",
            DeprecationWarning,
            stacklevel=3,
        )

    original_init = getattr(cls, "__init__")

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        for old, new in aliases.items():
            if old in kwargs:
                warn(old, new)
                kwargs[new] = kwargs.pop(old)
        original_init(self, *args, **kwargs)

    def __getattr__(self: Any, name: str) -> Any:
        new = aliases.get(name)
        if new is None:
            raise AttributeError(f"{cls.__name__!r} object has no attribute {name!r}")
        warn(name, new)
        return getattr(self, new)

    setattr(cls, "__init__", __init__)
    setattr(cls, "__getattr__", __getattr__)


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
