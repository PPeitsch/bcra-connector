"""The two analytics helpers are on their way out, and numpy with them (issue #149).

`get_variable_correlation()` and `generate_variable_report()` are the last methods on
`BCRAConnector` that were not already deprecated aliases. They stay until 1.0, warn, and
no longer need numpy for anything: the correlation runs on the standard library.
"""

import math
import sys
from datetime import date
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector
from bcra_connector.bcra_connector import _interpolate, _is_constant
from bcra_connector.principales_variables import DetalleMonetaria, PrincipalesVariables


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector(rate_limit=None)


def _series(values: List[float]) -> List[DetalleMonetaria]:
    """A series, newest first, as the API returns it."""
    return [
        DetalleMonetaria(fecha=date(2024, 1, len(values) - i), valor=v)
        for i, v in enumerate(values)
    ]


class TestTheWarning:
    """Both say they are going away, and that there is no replacement method."""

    def test_correlation_warns(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector.monetarias,
            "history",
            side_effect=[_series([1.0, 2.0, 3.0]), _series([2.0, 4.0, 6.0])],
        ):
            with pytest.warns(DeprecationWarning, match="removed in 1.0"):
                connector.get_variable_correlation("A", "B")

    def test_report_warns(self, connector: BCRAConnector) -> None:
        variable = PrincipalesVariables(id_variable=1, descripcion="Reservas")
        with patch.object(connector.monetarias, "find", return_value=variable):
            with patch.object(
                connector.monetarias, "history", return_value=_series([1.0, 2.0])
            ):
                with pytest.warns(DeprecationWarning, match="removed in 1.0"):
                    connector.generate_variable_report("Reservas")

    def test_the_message_points_at_the_documentation(
        self, connector: BCRAConnector
    ) -> None:
        """There is no `connector.x.y()` to send the caller to, unlike the aliases."""
        with patch.object(connector.monetarias, "history", return_value=[]):
            with pytest.warns(DeprecationWarning) as caught:
                connector.get_variable_correlation("A", "B")
        message = str(caught[0].message)
        assert "documentation" in message
        assert "use connector." not in message


class TestNoNumpy:
    """numpy is not a dependency of anything any more."""

    def test_it_is_not_in_the_manifest(self) -> None:
        """Read as text: `tomllib` is 3.11+, and the assertion needs no parser.

        Against `pyproject.toml` rather than the installed distribution's metadata,
        which only refreshes on reinstall and would make this pass or fail by
        accident of when the venv was last built.
        """
        manifest = (Path(__file__).parents[2] / "pyproject.toml").read_text()

        assert "numpy" not in manifest
        assert "scipy" not in manifest
        assert "analytics = [" not in manifest

    def test_the_correlation_runs_without_it(
        self, connector: BCRAConnector, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setitem(sys.modules, "numpy", None)
        with patch.object(
            connector.monetarias,
            "history",
            side_effect=[_series([1.0, 2.0, 3.0]), _series([2.0, 4.0, 6.0])],
        ):
            with pytest.deprecated_call():
                assert connector.get_variable_correlation("A", "B") == pytest.approx(
                    1.0
                )


class TestInterpolation:
    """`_interpolate` keeps the semantics numpy.interp had here."""

    XS = [10, 20, 40]
    YS = [1.0, 2.0, 4.0]

    @pytest.mark.parametrize(
        ("at", "expected"),
        [
            (10, 1.0),  # on the first point
            (40, 4.0),  # on the last
            (20, 2.0),  # on a middle point
            (15, 1.5),  # halfway between two
            (30, 3.0),  # halfway across the wider gap
            (5, 1.0),  # before the range: clamped, not extrapolated
            (99, 4.0),  # after the range: clamped
        ],
    )
    def test_samples(self, at: int, expected: float) -> None:
        assert _interpolate(self.XS, self.YS, [at]) == [pytest.approx(expected)]

    def test_unsorted_input(self) -> None:
        """The API returns series newest-first, so x arrives descending."""
        assert _interpolate([40, 20, 10], [4.0, 2.0, 1.0], [15]) == [pytest.approx(1.5)]

    def test_a_single_point_is_flat(self) -> None:
        assert _interpolate([10], [7.0], [1, 10, 99]) == [7.0, 7.0, 7.0]


class TestConstantCheck:
    """A constant series has no variance, so the correlation is undefined."""

    @pytest.mark.parametrize(
        ("values", "constant"),
        [
            ([1.0, 1.0, 1.0], True),
            ([1.0], True),
            ([0.0, 0.0], True),
            ([1.0, 1.0, 1.0 + 1e-15], True),  # floating-point noise, still constant
            ([1.0, 2.0], False),
            ([1.0, 1.0, 1.1], False),
        ],
    )
    def test_is_constant(self, values: List[float], constant: bool) -> None:
        assert _is_constant(values) is constant

    def test_a_constant_series_gives_nan(self, connector: BCRAConnector) -> None:
        with patch.object(
            connector.monetarias,
            "history",
            side_effect=[_series([5.0, 5.0, 5.0]), _series([1.0, 2.0, 3.0])],
        ):
            with pytest.deprecated_call():
                assert math.isnan(connector.get_variable_correlation("A", "B"))
