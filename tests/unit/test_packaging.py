"""The package ships what it promises (issue #137).

And only what it promises: the analytics that pulled numpy in is gone (issue #149).
"""

from importlib.resources import files
from pathlib import Path


def test_py_typed_is_part_of_the_package() -> None:
    """Without the PEP 561 marker, every annotation is invisible downstream.

    Type checkers ignore an installed package's annotations unless it ships
    ``py.typed``, so its absence silently turns `Page[T]`, `DateLike` and every
    model into ``Any`` for anyone who installs the library.
    """
    assert (files("bcra_connector") / "py.typed").is_file()


def test_numpy_is_not_in_the_manifest() -> None:
    """Read as text: `tomllib` is 3.11+, and the assertion needs no parser.

    Against `pyproject.toml` rather than the installed distribution's metadata,
    which only refreshes on reinstall and would make this pass or fail by
    accident of when the venv was last built.
    """
    manifest = (Path(__file__).parents[2] / "pyproject.toml").read_text()

    assert "numpy" not in manifest
    assert "scipy" not in manifest
    assert "analytics = [" not in manifest
