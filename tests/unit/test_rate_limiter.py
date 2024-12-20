"""Unit tests for the rate limiting functionality."""

import queue
import threading
import time
from typing import List, Optional, Tuple

import pytest

from bcra_connector.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimitConfig:
    """Test suite for RateLimitConfig class."""

    def test_valid_config(self) -> None:
        """Test valid rate limit configurations."""
        config: RateLimitConfig = RateLimitConfig(calls=10, period=1.0)
        assert config.calls == 10
        assert config.period == 1.0
        assert config.burst == 10  # Default burst equals calls

        config_with_burst: RateLimitConfig = RateLimitConfig(
            calls=10, period=1.0, _burst=20
        )
        assert config_with_burst.burst == 20

    def test_invalid_config(self) -> None:
        """Test invalid rate limit configurations."""
        with pytest.raises(ValueError, match="calls must be greater than 0"):
            RateLimitConfig(calls=0, period=1.0)

        with pytest.raises(ValueError, match="period must be greater than 0"):
            RateLimitConfig(calls=1, period=0)

        with pytest.raises(
            ValueError, match="burst must be greater than or equal to calls"
        ):
            RateLimitConfig(calls=10, period=1.0, _burst=5)


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    @pytest.fixture
    def limiter(self) -> RateLimiter:
        """Create a RateLimiter instance with default config."""
        config: RateLimitConfig = RateLimitConfig(calls=10, period=1.0, _burst=20)
        return RateLimiter(config)

    def test_basic_rate_limiting(self, limiter: RateLimiter) -> None:
        """Test basic rate limiting functionality."""
        # First 20 calls should be immediate (burst capacity)
        for _ in range(20):
            initial_delay: float = limiter.acquire()
            assert initial_delay == 0

        # Next call should be delayed
        start_time: float = time.monotonic()
        subsequent_delay: float = limiter.acquire()
        elapsed: float = time.monotonic() - start_time

        assert subsequent_delay > 0
        assert elapsed >= 0.1  # At least some delay

    def test_sliding_window(self, limiter: RateLimiter) -> None:
        """Test sliding window behavior."""
        # Use up initial burst
        for _ in range(20):
            limiter.acquire()

        # Wait half the period
        time.sleep(0.5)

        # Should still be limited
        first_delay: float = limiter.acquire()
        assert first_delay > 0

        # Wait full period
        time.sleep(1.0)

        # Should be allowed again
        second_delay: float = limiter.acquire()
        assert second_delay == 0

    def test_reset(self, limiter: RateLimiter) -> None:
        """Test reset functionality."""
        # Use up some capacity
        for _ in range(15):
            limiter.acquire()

        assert limiter.current_usage == 15

        # Reset the limiter
        limiter.reset()

        # Should be back to initial state
        assert limiter.current_usage == 0
        delay: float = limiter.acquire()
        assert delay == 0

    def test_concurrent_access(self, limiter: RateLimiter) -> None:
        """Test thread safety of rate limiter."""
        results_queue: queue.Queue = queue.Queue()
        expected_immediate = limiter.config.burst
        total_threads = expected_immediate + 5

        def worker() -> None:
            try:
                delay = limiter.acquire()
                results_queue.put(("success", delay))
            except Exception as e:
                results_queue.put(("error", str(e)))

        threads = [
            threading.Thread(target=worker)
            for _ in range(total_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        immediate = sum(1 for status, delay in results_queue.queue if delay == 0)
        assert immediate == expected_immediate

    def test_remaining_calls(self, limiter: RateLimiter) -> None:
        """Test remaining calls calculation."""
        assert limiter.remaining_calls() == 10  # Initial capacity

        # Use some capacity
        limiter.acquire()
        assert limiter.remaining_calls() == 9

        # Use all remaining initial capacity
        for _ in range(9):
            limiter.acquire()
        assert limiter.remaining_calls() == 0

    def test_is_limited_property(self, limiter: RateLimiter) -> None:
        """Test is_limited property behavior."""
        assert not limiter.is_limited

        # Use up initial capacity
        for _ in range(20):
            limiter.acquire()

        assert limiter.is_limited

        # Wait for reset
        time.sleep(1.1)  # type: ignore[unreachable]
        assert not limiter.is_limited

    @pytest.mark.timeout(5)
    def test_burst_behavior(self) -> None:
        """Test burst capacity behavior."""
        # Create limiter with burst capacity
        config: RateLimitConfig = RateLimitConfig(calls=5, period=1.0, _burst=10)
        limiter: RateLimiter = RateLimiter(config)

        # Should allow burst capacity immediately
        for _ in range(10):
            initial_delay: float = limiter.acquire()
            assert initial_delay == 0

        # Next calls should be rate limited
        subsequent_delay: float = limiter.acquire()
        assert subsequent_delay > 0

    def test_rate_limit_precision(self, limiter: RateLimiter) -> None:
        """Test precision of rate limiting delays."""
        # Use up burst capacity
        for _ in range(20):
            limiter.acquire()

        # Test subsequent requests
        delays = []
        for _ in range(5):
            start = time.monotonic()
            delay = limiter.acquire()
            actual_delay = time.monotonic() - start
            delays.append(actual_delay)

        # Verify delays are reasonably close to expected
        for i in range(1, len(delays)):
            diff = abs(delays[i] - delays[i - 1])
            assert diff < 0.2  # Allow more tolerance
