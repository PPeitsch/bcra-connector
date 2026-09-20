"""Tests for the connector's logging behaviour: library defaults and PII redaction."""

import logging
from typing import Iterator
from unittest.mock import Mock, patch

import pytest
import requests

from bcra_connector import BCRAConnector
from bcra_connector.bcra_connector import _has_active_handler, _redact

CUIT = "20123456789"
LOGGER_NAME = "bcra_connector.bcra_connector"


@pytest.fixture
def isolated_logger() -> Iterator[logging.Logger]:
    """Give the connector logger a clean state and restore it afterwards.

    ``propagate`` is disabled so pytest's own capture handlers on the root logger
    don't count as "configured by the application".
    """
    logger = logging.getLogger(LOGGER_NAME)
    saved = (logger.level, list(logger.handlers), logger.propagate)
    logger.setLevel(logging.NOTSET)
    logger.handlers.clear()
    logger.propagate = False
    yield logger
    logger.setLevel(saved[0])
    logger.handlers[:] = saved[1]
    logger.propagate = saved[2]


def _response(data: dict, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.url = f"https://api.bcra.gob.ar/CentralDeDeudores/v1.0/Deudas/{CUIT}"
    response.reason = "Service Unavailable" if status_code >= 500 else "OK"
    response.json.return_value = data
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    else:
        response.raise_for_status.return_value = None
    return response


DEUDAS_OK = {
    "status": 200,
    "results": {
        "identificacion": int(CUIT),
        "denominacion": "JUAN PEREZ",
        "periodos": [],
    },
}


class TestLibraryLoggingDefaults:
    def test_package_logger_has_null_handler(self) -> None:
        handlers = logging.getLogger("bcra_connector").handlers
        assert any(isinstance(h, logging.NullHandler) for h in handlers)

    def test_default_does_not_configure_logging(
        self, isolated_logger: logging.Logger
    ) -> None:
        BCRAConnector()
        assert isolated_logger.handlers == []
        assert isolated_logger.level == logging.NOTSET

    def test_default_does_not_reset_level_set_by_application(
        self, isolated_logger: logging.Logger
    ) -> None:
        isolated_logger.setLevel(logging.WARNING)
        BCRAConnector()
        assert isolated_logger.level == logging.WARNING

    def test_debug_opt_in_adds_single_stderr_handler(
        self, isolated_logger: logging.Logger
    ) -> None:
        BCRAConnector(debug=True)
        BCRAConnector(debug=True)
        assert isolated_logger.level == logging.DEBUG
        assert len(isolated_logger.handlers) == 1
        assert isinstance(isolated_logger.handlers[0], logging.StreamHandler)

    def test_debug_does_not_duplicate_application_handler(
        self, isolated_logger: logging.Logger
    ) -> None:
        app_handler = logging.StreamHandler()
        isolated_logger.addHandler(app_handler)
        BCRAConnector(debug=True)
        assert isolated_logger.handlers == [app_handler]


class TestHasActiveHandler:
    def test_null_handler_does_not_count(self) -> None:
        logger = logging.getLogger("bcra_test.null_only")
        logger.propagate = False
        logger.addHandler(logging.NullHandler())
        assert not _has_active_handler(logger)

    def test_no_handler_up_to_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # pytest attaches capture handlers to the root logger; hide them.
        monkeypatch.setattr(logging.getLogger(), "handlers", [])
        assert not _has_active_handler(logging.getLogger("bcra_test.orphan"))

    def test_handler_on_ancestor_counts(self) -> None:
        parent = logging.getLogger("bcra_test.parent")
        parent.propagate = False
        parent.addHandler(logging.StreamHandler())
        assert _has_active_handler(logging.getLogger("bcra_test.parent.child"))


class TestRedaction:
    @pytest.mark.parametrize(
        "text, expected",
        [
            (f"/Deudas/{CUIT}", "/Deudas/20********9"),
            (f"/Deudas/Historicas/{CUIT}?x=1", "/Deudas/Historicas/20********9?x=1"),
            ("/Monetarias/1?Limit=10", "/Monetarias/1?Limit=10"),
            ("123456789012", "123456789012"),  # 12 digits: not an identifier
        ],
    )
    def test_redact(self, text: str, expected: str) -> None:
        assert _redact(text) == expected

    def test_deudas_logs_contain_no_personal_data(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        connector = BCRAConnector()
        with (
            patch.object(
                connector.session,
                "get",
                side_effect=[_response({}, 503), _response(DEUDAS_OK)],
            ),
            patch("bcra_connector._http.time.sleep"),
        ):
            with caplog.at_level(logging.DEBUG, logger="bcra_connector"):
                connector.deudores.debts(CUIT)

        messages = "\n".join(r.getMessage() for r in caplog.records)
        assert "Transient HTTP 503" in messages  # the retry path was logged
        assert CUIT not in messages
        assert "JUAN PEREZ" not in messages
