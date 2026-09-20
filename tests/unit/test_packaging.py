"""The package ships what it promises (issue #137)."""

from importlib.resources import files


def test_py_typed_is_part_of_the_package() -> None:
    """Without the PEP 561 marker, every annotation is invisible downstream.

    Type checkers ignore an installed package's annotations unless it ships
    ``py.typed``, so its absence silently turns `Page[T]`, `DateLike` and every
    model into ``Any`` for anyone who installs the library.
    """
    assert (files("bcra_connector") / "py.typed").is_file()
