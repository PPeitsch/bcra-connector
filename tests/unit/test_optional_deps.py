"""The whole library works without numpy or scipy: neither is a dependency."""

import subprocess
import sys

BLOCK_NUMERIC = (
    "import sys\n"
    "sys.modules['numpy'] = None\n"
    "sys.modules['scipy'] = None\n"
    "import bcra_connector\n"
    "from bcra_connector import BCRAConnector\n"
    "BCRAConnector()\n"
    "print('ok')\n"
)


def test_import_without_numpy_or_scipy() -> None:
    result = subprocess.run(
        [sys.executable, "-c", BLOCK_NUMERIC],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
