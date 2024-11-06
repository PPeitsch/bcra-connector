"""Rate limiting functionality for API requests."""

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional
from threading import Lock


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.
    
    :param calls: Maximum number of calls allowed in the time period
    :param period: Time period in seconds
    :param burst: Maximum number of calls allowed in quick succession (burst limit)
    """
    calls: int
    period: float
    burst: Optional[int] = None

    def __post_init__(self):
        """Validate and set defaults for rate limit configuration."""
        if self.calls <= 0:
            raise ValueError("calls must be greater than 0")
        if self.period <= 0:
            raise ValueError("period must be greater than 0")
        if self.burst is not None and self.burst <= 0:
            raise ValueError("burst must be greater than 0")
        if self.burst is not None and self.burst < self.calls:
            raise ValueError("burst must be greater than or equal to calls")
        
        # If burst is not set, use calls as burst limit
        if self.burst is None:
            self.burst = self.calls


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
        """Calculate the required delay before the next request."""
        if not self._window:
            return 0.0

        now = time.monotonic()
        self._clean_old_timestamps()

        # If we haven't hit the burst limit, no delay needed
        if len(self._window) < self.config.burst:
            return 0.0

        # If we've hit the rate limit, calculate delay
        if len(self._window) >= self.config.calls:
            oldest_timestamp = self._window[-self.config.calls]
            next_available = oldest_timestamp + self.config.period
            delay = next_available - now
            return max(0.0, delay)

        return 0.0

    def acquire(self) -> float:
        """Acquire permission to make a request.
        
        :return: Time spent waiting (in seconds)
        """
        with self._lock:
            delay = self._get_delay()
            if delay > 0:
                time.sleep(delay)

            now = time.monotonic()
            self._window.append(now)
            return delay

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
            return len(self._window) >= self.config.calls

    def remaining_calls(self) -> int:
        """Get the number of remaining calls allowed in the current window."""
        with self._lock:
            self._clean_old_timestamps()
            return max(0, self.config.calls - len(self._window))