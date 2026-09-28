"""
Rate limiting functionality for API requests.
"""

import math
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    ``calls`` per ``period`` is the sustained rate. ``_burst`` is how many calls can go
    out back to back after the limiter has been idle; it defaults to ``calls``.

    :param calls: Number of calls allowed per period, sustained
    :param period: Time period in seconds
    :param _burst: Calls allowed back to back after an idle spell (internal)
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
    """Token bucket: holds up to ``burst`` tokens and earns ``calls`` per ``period``.

    Each request takes a token. When none is left, :meth:`acquire` takes it anyway (the
    balance goes negative) and returns how long the caller has to wait for it, so
    concurrent callers line up one token apart instead of all waking at once.
    """

    def __init__(self, config: RateLimitConfig):
        """Initialize the rate limiter with a full bucket.

        :param config: Rate limit configuration
        """
        self.config = config
        self._lock = Lock()
        self._tokens = float(config.burst)
        self._updated = monotonic()

    @property
    def _rate(self) -> float:
        """Tokens earned per second."""
        return self.config.calls / self.config.period

    def _refill(self) -> None:
        """Add the tokens earned since the last update, up to ``burst``."""
        now = monotonic()
        earned = (now - self._updated) * self._rate
        self._tokens = min(float(self.config.burst), self._tokens + earned)
        self._updated = now

    def acquire(self) -> float:
        """Take a token for one request.

        The token is taken even when the caller has to wait for it: the caller must
        sleep the returned delay before sending the request.

        :return: Seconds to wait before sending the request (0 if a token was free)
        """
        with self._lock:
            self._refill()
            self._tokens -= 1
            if self._tokens >= 0:
                return 0.0
            return -self._tokens / self._rate

    def reset(self) -> None:
        """Reset the rate limiter to a full bucket."""
        with self._lock:
            self._tokens = float(self.config.burst)
            self._updated = monotonic()

    @property
    def current_usage(self) -> int:
        """Get the number of tokens taken and not earned back yet.

        Includes the requests still waiting for theirs, so it can exceed ``burst``.
        """
        with self._lock:
            self._refill()
            return max(0, math.ceil(self.config.burst - self._tokens))

    @property
    def is_limited(self) -> bool:
        """Check whether the next request would have to wait."""
        with self._lock:
            self._refill()
            return self._tokens < 1

    def remaining_calls(self) -> int:
        """Get the number of requests that can go out right now without waiting."""
        with self._lock:
            self._refill()
            return max(0, math.floor(self._tokens))
