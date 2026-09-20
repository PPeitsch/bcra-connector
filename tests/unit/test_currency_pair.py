"""cambiarias.pair(): BASE/QUOTE convention and currencies without tipoCotizacion."""

from datetime import date
from typing import Dict, List, Tuple
from unittest.mock import patch

import pytest

from bcra_connector import BCRAConnector
from bcra_connector.estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha

D1 = date(2026, 9, 17)
D2 = date(2026, 9, 18)

# Live values (tipoPase, tipoCotizacion) from Cotizaciones on 2026-09-18.
LIVE: Dict[str, Tuple[float, float]] = {
    "USD": (0.0, 1514.5),
    "EUR": (1.1481, 1738.79745),
    "JPY": (0.006382, 9.666199),
    "XAU": (4392.24, 0.0),
    "ARS": (0.00066, 0.0),
    "REF": (0.0, 1512.3332),
}


def _series(code: str) -> List[CotizacionFecha]:
    pase, cotizacion = LIVE[code]
    # Newest first, as the API returns it.
    return [
        CotizacionFecha(
            fecha=d,
            detalle=[CotizacionDetalle(code, code, pase, cotizacion)],
        )
        for d in (D2, D1)
    ]


@pytest.fixture
def connector() -> BCRAConnector:
    return BCRAConnector(rate_limit=None)


def _pair(connector: BCRAConnector, base: str, quote: str) -> Tuple[float, List[str]]:
    """Return the rate on D2 and the currencies that were requested."""
    with patch.object(
        connector.cambiarias,
        "evolution",
        side_effect=lambda code, *a, **k: _series(code),
    ) as mock_evolution:
        result = connector.cambiarias.pair(base, quote, days=2)
    assert [r["fecha"] for r in result] == [D1, D2]
    return result[-1]["tasa"], [c.args[0] for c in mock_evolution.call_args_list]


@pytest.mark.parametrize(
    "base,quote,expected",
    [
        ("USD", "EUR", 1 / 1.1481),  # EUR per USD
        ("EUR", "USD", 1.1481),  # USD per EUR
        ("USD", "ARS", 1514.5),  # ARS per USD
        ("EUR", "ARS", 1.1481 * 1514.5),  # ~ tipoCotizacion of EUR
        ("ARS", "USD", 1 / 1514.5),
        ("USD", "XAU", 1 / 4392.24),  # troy oz per USD
        ("EUR", "JPY", 1.1481 / 0.006382),
    ],
)
def test_amount_of_quote_for_one_base(
    connector: BCRAConnector, base: str, quote: str, expected: float
) -> None:
    rate, _ = _pair(connector, base, quote)
    assert rate == pytest.approx(expected)


def test_same_currency_is_one(connector: BCRAConnector) -> None:
    assert _pair(connector, "EUR", "EUR")[0] == 1.0
    assert _pair(connector, "USD", "USD")[0] == 1.0


@pytest.mark.parametrize(
    "base,quote,requested",
    [
        ("USD", "EUR", ["EUR"]),
        ("EUR", "USD", ["EUR"]),
        ("USD", "ARS", ["USD"]),
        ("EUR", "ARS", ["EUR", "USD"]),
        ("EUR", "JPY", ["EUR", "JPY"]),
        ("EUR", "EUR", ["EUR"]),
        ("USD", "USD", ["USD"]),
    ],
)
def test_requests_only_what_is_needed(
    connector: BCRAConnector, base: str, quote: str, requested: List[str]
) -> None:
    assert _pair(connector, base, quote)[1] == requested


def test_currency_without_usd_rate_is_skipped(
    connector: BCRAConnector, caplog: pytest.LogCaptureFixture
) -> None:
    with patch.object(
        connector.cambiarias,
        "evolution",
        side_effect=lambda code, *a, **k: _series(code),
    ):
        assert connector.cambiarias.pair("REF", "EUR", days=2) == []
    assert "REF" in caplog.text


def test_missing_dates_are_skipped(connector: BCRAConnector) -> None:
    def evolution(code: str, *args: object, **kwargs: object) -> List[CotizacionFecha]:
        series = _series(code)
        return series if code == "EUR" else series[:1]  # JPY only has D2

    with patch.object(connector.cambiarias, "evolution", side_effect=evolution):
        result = connector.cambiarias.pair("EUR", "JPY", days=2)
    assert [r["fecha"] for r in result] == [D2]


def test_entries_without_date_are_ignored(connector: BCRAConnector) -> None:
    def evolution(code: str, *args: object, **kwargs: object) -> List[CotizacionFecha]:
        return _series(code) + [CotizacionFecha(fecha=None, detalle=[])]

    with patch.object(connector.cambiarias, "evolution", side_effect=evolution):
        result = connector.cambiarias.pair("USD", "EUR", days=2)
    assert len(result) == 2


def test_codes_are_case_insensitive(connector: BCRAConnector) -> None:
    rate, requested = _pair(connector, "usd", "eur")
    assert rate == pytest.approx(1 / 1.1481)
    assert requested == ["EUR"]
