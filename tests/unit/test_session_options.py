"""verify_ssl with a CA bundle, User-Agent and session lifecycle."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bcra_connector import BCRAConnector, __version__


def _request_verify(connector: BCRAConnector) -> object:
    response = Mock()
    response.json.return_value = {"results": []}
    with patch.object(connector.session, "get", return_value=response) as mock_get:
        connector._make_request("test")
    return mock_get.call_args.kwargs["verify"]


class TestVerify:
    def test_default_verifies(self) -> None:
        assert _request_verify(BCRAConnector()) is True

    def test_ca_bundle_path_is_passed_to_requests(self, tmp_path: Path) -> None:
        bundle = tmp_path / "corp-ca.pem"
        bundle.write_text("-----BEGIN CERTIFICATE-----\n")
        assert _request_verify(BCRAConnector(verify_ssl=str(bundle))) == str(bundle)
        # os.PathLike is accepted too and passed on as a string
        assert _request_verify(BCRAConnector(verify_ssl=bundle)) == str(bundle)

    def test_missing_ca_bundle_fails_early(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="CA bundle"):
            BCRAConnector(verify_ssl=str(tmp_path / "missing.pem"))

    def test_ca_bundle_does_not_warn(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        bundle = tmp_path / "corp-ca.pem"
        bundle.write_text("")
        BCRAConnector(verify_ssl=str(bundle))
        assert "SSL verification is disabled" not in caplog.text


def test_user_agent_has_real_version() -> None:
    agent = BCRAConnector().session.headers["User-Agent"]
    assert agent == f"bcra-connector/{__version__}"


class TestLifecycle:
    def test_close_closes_session(self) -> None:
        connector = BCRAConnector()
        with patch.object(connector.session, "close") as mock_close:
            connector.close()
        mock_close.assert_called_once()

    def test_context_manager(self) -> None:
        connector = BCRAConnector()
        with patch.object(connector.session, "close") as mock_close:
            with connector as entered:
                assert entered is connector
                mock_close.assert_not_called()
        mock_close.assert_called_once()

    def test_context_manager_closes_on_error(self) -> None:
        connector = BCRAConnector()
        with patch.object(connector.session, "close") as mock_close:
            with pytest.raises(RuntimeError):
                with connector:
                    raise RuntimeError("boom")
        mock_close.assert_called_once()
