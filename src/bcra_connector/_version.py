"""Version information.

This project uses semantic versioning (see https://semver.org/):
MAJOR.MINOR.PATCH

- MAJOR version for incompatible API changes
- MINOR version for added functionality in a backward compatible manner
- PATCH version for backward compatible bug fixes
"""

import re
from typing import NamedTuple


class Version(NamedTuple):
    """Version information as a named tuple."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        """Return the version string."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_str(cls, version_str: str) -> "Version":
        """Create a Version instance from a string."""
        if not cls.is_valid(version_str):
            raise ValueError(
                f"Invalid version format: {version_str}. "
                "Version must follow semantic versioning X.Y.Z"
            )
        major, minor, patch = map(int, version_str.split("."))
        return cls(major, minor, patch)

    @staticmethod
    def is_valid(version_str: str) -> bool:
        """Check if a version string is valid."""
        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version_str))

    def to_dev_version(self) -> str:
        """Convert to a development version string."""
        return f"{self}.dev0"

    def to_rc_version(self, rc_number: int) -> str:
        """Convert to a release candidate version string."""
        return f"{self}rc{rc_number}"

    def increment_major(self) -> "Version":
        """Create a new Version with incremented major version."""
        return Version(self.major + 1, 0, 0)

    def increment_minor(self) -> "Version":
        """Create a new Version with incremented minor version."""
        return Version(self.major, self.minor + 1, 0)

    def increment_patch(self) -> "Version":
        """Create a new Version with incremented patch version."""
        return Version(self.major, self.minor, self.patch + 1)

    def is_compatible_with(self, other: "Version") -> bool:
        """Check if this version is compatible with another version."""
        return self.major == other.major


__version__ = "0.3.3"
version_info = Version.from_str(__version__)

# Useful constants for version comparison
MINIMUM_SUPPORTED_VERSION = Version(0, 1, 0)
CURRENT_VERSION = version_info
