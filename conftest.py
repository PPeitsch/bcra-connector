import sys
from pathlib import Path

# Add src directory to path to make bcra_connector importable
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path.resolve()))
