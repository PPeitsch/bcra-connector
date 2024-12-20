from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)  # frozen=True hace la clase inmutable
class TimeoutConfig:
    """Configuration for request timeouts.

    :param connect: How long to wait for the connection to be established (seconds)
    :param read: How long to wait for the server to send data (seconds)
    """

    connect: float = field(default=3.05)
    read: float = field(default=27.0)

    def __post_init__(self) -> None:
        """Validate timeout values."""
        if self.connect <= 0:
            raise ValueError("connect timeout must be greater than 0")
        if self.read <= 0:
            raise ValueError("read timeout must be greater than 0")

    @property
    def as_tuple(self) -> Tuple[float, float]:
        """Get timeout configuration as a tuple.

        :return: Tuple of (connect_timeout, read_timeout)
        """
        return self.connect, self.read

    @classmethod
    def from_total(cls, total: float) -> "TimeoutConfig":
        """Create a TimeoutConfig from a total timeout value.

        :param total: Total timeout in seconds, will be split between connect and read
        :return: TimeoutConfig instance
        :raises ValueError: If total timeout is less than or equal to 0
        """
        if total <= 0:
            raise ValueError("total timeout must be greater than 0")
        # Allocate 10% to connect timeout and 90% to read timeout
        return cls(connect=total * 0.1, read=total * 0.9)

    @classmethod
    def default(cls) -> "TimeoutConfig":
        """Get the default timeout configuration.

        :return: TimeoutConfig instance with default values
        """
        return cls()

    def __str__(self) -> str:
        """Get string representation of timeout configuration."""
        return f"TimeoutConfig(connect={self.connect:.2f}s, read={self.read:.2f}s)"
