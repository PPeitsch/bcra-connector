"""Tests for the shared date normalization helper."""

from datetime import date, datetime

import pytest

from bcra_connector.models import as_date


class TestAccepted:
    """Every type the public API's date inputs accept."""

    def test_date_passes_through(self) -> None:
        assert as_date(date(2024, 1, 2), "fecha") == date(2024, 1, 2)

    def test_datetime_drops_the_time(self) -> None:
        assert as_date(datetime(2024, 1, 2, 15, 30), "fecha") == date(2024, 1, 2)

    def test_iso_string(self) -> None:
        assert as_date("2024-01-02", "fecha") == date(2024, 1, 2)

    def test_iso_datetime_string(self) -> None:
        assert as_date("2024-01-02T15:30:00", "fecha") == date(2024, 1, 2)

    def test_surrounding_whitespace_is_ignored(self) -> None:
        assert as_date("  2024-01-02 ", "fecha") == date(2024, 1, 2)


class TestRejected:
    """A bad date fails here, naming the parameter, not at the API."""

    @pytest.mark.parametrize(
        "value", ["02/01/2024", "2024-13-01", "yesterday", "", "20240102x"]
    )
    def test_non_iso_string_raises_value_error(self, value: str) -> None:
        with pytest.raises(ValueError, match="'fecha' must be an ISO 8601 date"):
            as_date(value, "fecha")

    def test_error_quotes_the_offending_value(self) -> None:
        with pytest.raises(ValueError, match="'02/01/2024'"):
            as_date("02/01/2024", "fecha")

    @pytest.mark.parametrize("value", [20240102, 1.5, None, ["2024-01-02"]])
    def test_other_types_raise_type_error(self, value: object) -> None:
        with pytest.raises(TypeError, match="'desde' must be a date"):
            as_date(value, "desde")

    def test_type_error_names_the_type(self) -> None:
        with pytest.raises(TypeError, match="got int"):
            as_date(20240102, "desde")
