"""
Rate limiting functionality for API requests.
"""

import time
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Deque, Optional

from bcra_connector import BCRAApiError


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    :param calls: Number of calls allowed per period
    :param period: Time period in seconds
    :param _burst: Maximum number of calls allowed in burst (internal)
    """

    calls: int
    period: float
    _burst: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate rate limit configuration."""
        if self.calls <= 0:
            raise ValueError("calls must be greater than 0")
        if self.period <= 0:
            raise ValueError("period must be greater than 0")
        if self._burst is not None and self._burst < self.calls:
            raise ValueError("burst must be greater than or equal to calls")

        # If burst is not specified, use calls as the burst limit
        if self._burst is None:
            self._burst = self.calls

    @property
    def burst(self) -> int:
        """Burst limit is always an int after initialization."""
        assert self._burst is not None
        return self._burst


class RateLimiter:
    """Rate limiter using token bucket algorithm with sliding window."""

    def __init__(self, config: RateLimitConfig):
        """Initialize the rate limiter.

        :param config: Rate limit configuration
        """
        self.config = config
        self._window: Deque[float] = deque()
        self._lock = Lock()
        self._last_check = time.monotonic()

    def _clean_old_timestamps(self) -> None:
        """Remove timestamps outside the current window."""
        now = time.monotonic()
        while self._window and now - self._window[0] > self.config.period:
            self._window.popleft()

    def _get_delay(self) -> float:
        """Calculate the required delay before the next request.

        :return: Required delay in seconds
        """
        now = time.monotonic()
        self._clean_old_timestamps()

        if len(self._window) < self.config.burst:
            return 0.0

        # Calculate delay based on the period and number of requests beyond burst
        requests_over_burst = max(0, len(self._window) - self.config.calls)
        if requests_over_burst > 0:
            # Calculate delay that distributes requests evenly over the period
            next_available = self._window[0] + (
                self.config.period * requests_over_burst / self.config.calls
            )
            return max(0.0, next_available - now)

        # Default delay when at burst limit
        return max(0.0, self._window[0] + self.config.period - now)

    def acquire(self) -> float:
        """Acquire permission to make a request.

        Enforces rate limiting using a sliding window approach. If the rate limit is exceeded,
        it will either delay the request or raise an exception depending on the severity.

        :return: Time spent waiting (in seconds)
        :raises BCRAApiError: If rate limit is exceeded beyond burst capacity
        """
        with self._lock:
            now = time.monotonic()

            # Clean old timestamps first
            self._clean_old_timestamps()

            # Check burst limit
            if len(self._window) >= self.config.burst:
                raise BCRAApiError(
                    f"Rate limit exceeded: Maximum burst capacity of {self.config.burst} requests reached"
                )

            # Calculate required delay based on standard rate limit
            if len(self._window) >= self.config.calls:
                # Calculate when the oldest request in the rate limit window will expire
                # Add a small buffer (0.01s) to ensure we're safely under the limit
                delay = (self._window[0] + self.config.period + 0.01) - now
                if delay > 0:
                    return delay

            # Add current request timestamp and return 0 delay
            self._window.append(now)
            return 0.0

    def reset(self) -> None:
        """Reset the rate limiter state."""
        with self._lock:
            self._window.clear()
            self._last_check = time.monotonic()

    @property
    def current_usage(self) -> int:
        """Get the current number of requests in the window."""
        with self._lock:
            self._clean_old_timestamps()
            return len(self._window)

    @property
    def is_limited(self) -> bool:
        """Check if rate limit is currently being enforced."""
        with self._lock:
            self._clean_old_timestamps()
            current_size = len(self._window)
            return bool(
                current_size >= self.config.burst
                or (
                    current_size >= self.config.calls
                    and self._window
                    and (time.monotonic() - self._window[0]) <= self.config.period
                )
            )

    def remaining_calls(self) -> int:
        """Get the number of remaining calls allowed in the current window.

        Based on the base rate limit (calls), not the burst limit.
        """
        with self._lock:
            self._clean_old_timestamps()
            return max(0, self.config.calls - len(self._window))
