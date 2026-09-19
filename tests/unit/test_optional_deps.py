"""The connector must work without numpy/scipy; only analytics need numpy."""

import math
import subprocess
import sys
from datetime import date
from typing import List
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector
from bcra_connector.principales_variables import DetalleMonetaria, PrincipalesVariables

BLOCK_NUMERIC = (
    "import sys\n"
    "sys.modules['numpy'] = None\n"
    "sys.modules['scipy'] = None\n"
    "import bcra_connector\n"
    "from bcra_connector import BCRAConnector\n"
    "BCRAConnector()\n"
    "print('ok')\n"
)


def _series() -> List[DetalleMonetaria]:
    # Newest first, as the API returns it.
    return [
        DetalleMonetaria(fecha=date(2024, 1, 4), valor=40.0),
        DetalleMonetaria(fecha=date(2024, 1, 3), valor=10.0),
        DetalleMonetaria(fecha=date(2024, 1, 2), valor=30.0),
        DetalleMonetaria(fecha=date(2024, 1, 1), valor=20.0),
    ]


def test_import_without_numpy_or_scipy() -> None:
    result = subprocess.run(
        [sys.executable, "-c", BLOCK_NUMERIC],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_report_without_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "numpy", None)
    connector = BCRAConnector(rate_limit=None)
    variable = PrincipalesVariables(idVariable=1, descripcion="Reservas")
    with patch.object(connector, "get_variable_by_name", return_value=variable):
        with patch.object(connector, "get_variable_history", return_value=_series()):
            report = connector.generate_variable_report("Reservas", days=4)

    assert report["start_date"] == "2024-01-01"
    assert report["latest_value"] == 40.0
    assert report["percent_change"] == pytest.approx(100.0)
    assert report["mean_value"] == pytest.approx(25.0)
    assert report["median_value"] == pytest.approx(25.0)
    assert report["min_value"] == 10.0
    assert report["max_value"] == 40.0
    # Population standard deviation, as np.std computed it.
    assert report["std_dev"] == pytest.approx(math.sqrt(125.0))
    assert report["data_points"] == 4


def test_correlation_without_numpy_asks_for_extra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "numpy", None)
    connector = BCRAConnector(rate_limit=None)
    with patch.object(connector, "get_variable_history", return_value=_series()):
        with pytest.raises(ImportError, match=r"bcra-connector\[analytics\]"):
            connector.get_variable_correlation("A", "B")


def test_correlation_matches_pearson() -> None:
    pytest.importorskip("numpy")
    connector = BCRAConnector(rate_limit=None)
    other = [
        DetalleMonetaria(fecha=d.fecha, valor=v)
        for d, v in zip(_series(), [1.0, 2.0, 4.0, 3.0])
    ]
    with patch.object(
        connector, "get_variable_history", side_effect=[_series(), other]
    ):
        corr = connector.get_variable_correlation("A", "B", days=4)

    # Pearson r of (20, 30, 10, 40) vs (3, 4, 2, 1), oldest first.
    assert corr == pytest.approx(-0.2)
