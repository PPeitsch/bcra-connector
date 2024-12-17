"""Unit tests for the rate limiting functionality."""

import time
from datetime import datetime
from unittest.mock import patch

import pytest
from bcra_connector.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimitConfig:
    """Test suite for RateLimitConfig class."""

    def test_valid_config(self):
        """Test valid rate limit configurations."""
        config = RateLimitConfig(calls=10, period=1.0)
        assert config.calls == 10
        assert config.period == 1.0
        assert config.burst == 10  # Default burst equals calls

        config = RateLimitConfig(calls=10, period=1.0, _burst=20)
        assert config.burst == 20

    def test_invalid_config(self):
        """Test invalid rate limit configurations."""
        with pytest.raises(ValueError, match="calls must be greater than 0"):
            RateLimitConfig(calls=0, period=1.0)

        with pytest.raises(ValueError, match="period must be greater than 0"):
            RateLimitConfig(calls=1, period=0)

        with pytest.raises(ValueError, match="burst must be greater than or equal to calls"):
            RateLimitConfig(calls=10, period=1.0, _burst=5)


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create a RateLimiter instance with default config."""
        config = RateLimitConfig(calls=10, period=1.0, _burst=20)
        return RateLimiter(config)

    def test_basic_rate_limiting(self, limiter):
        """Test basic rate limiting functionality."""
        # First 20 calls should be immediate (burst capacity)
        for _ in range(20):
            delay = limiter.acquire()
            assert delay == 0

        # Next call should be delayed
        start_time = time.monotonic()
        delay = limiter.acquire()
        elapsed = time.monotonic() - start_time

        assert delay > 0
        assert elapsed >= 0.1  # At least some delay

    def test_sliding_window(self, limiter):
        """Test sliding window behavior."""
        # Use up initial burst
        for _ in range(20):
            limiter.acquire()

        # Wait half the period
        time.sleep(0.5)

        # Should still be limited
        delay = limiter.acquire()
        assert delay > 0

        # Wait full period
        time.sleep(1.0)

        # Should be allowed again
        delay = limiter.acquire()
        assert delay == 0

    def test_reset(self, limiter):
        """Test reset functionality."""
        # Use up some capacity
        for _ in range(15):
            limiter.acquire()

        assert limiter.current_usage == 15

        # Reset the limiter
        limiter.reset()

        # Should be back to initial state
        assert limiter.current_usage == 0
        delay = limiter.acquire()
        assert delay == 0

    def test_concurrent_access(self, limiter):
        """Test thread safety of rate limiter."""
        import threading
        import queue

        results = queue.Queue()

        def worker():
            try:
                delay = limiter.acquire()
                results.put(("success", delay))
            except Exception as e:
                results.put(("error", str(e)))

        # Launch multiple threads simultaneously
        threads = []
        for _ in range(25):  # More than burst limit
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Collect results
        success_count = 0
        delayed_count = 0
        while not results.empty():
            status, delay = results.get()
            assert status == "success"  # No errors should occur
            if delay == 0:
                success_count += 1
            else:
                delayed_count += 1

        assert success_count == 20  # Burst limit
        assert delayed_count == 5  # Remaining requests

    def test_remaining_calls(self, limiter):
        """Test remaining calls calculation."""
        assert limiter.remaining_calls() == 10  # Initial capacity

        # Use some capacity
        limiter.acquire()
        assert limiter.remaining_calls() == 9

        # Use all remaining initial capacity
        for _ in range(9):
            limiter.acquire()
        assert limiter.remaining_calls() == 0

    def test_is_limited_property(self, limiter):
        """Test is_limited property behavior."""
        assert not limiter.is_limited

        # Use up initial capacity
        for _ in range(20):
            limiter.acquire()

        assert limiter.is_limited

        # Wait for reset
        time.sleep(1.1)
        assert not limiter.is_limited

    @patch('time.monotonic')
    def test_window_cleanup(self, mock_time, limiter):
        """Test cleanup of old timestamps from the window."""
        current_time = 1000.0
        mock_time.return_value = current_time

        # Add some requests
        for _ in range(5):
            limiter.acquire()
            current_time += 0.1
            mock_time.return_value = current_time

        assert len(limiter._window) == 5

        # Move time forward past the window
        current_time += 2.0  # Past the 1-second window
        mock_time.return_value = current_time

        # Next acquire should clean old timestamps
        limiter.acquire()
        assert len(limiter._window) == 1  # Only the new timestamp remains

    def test_burst_behavior(self):
        """Test burst capacity behavior."""
        # Create limiter with burst capacity
        config = RateLimitConfig(calls=5, period=1.0, _burst=10)
        limiter = RateLimiter(config)

        # Should allow burst capacity immediately
        for _ in range(10):
            delay = limiter.acquire()
            assert delay == 0

        # Next calls should be rate limited
        delay = limiter.acquire()
        assert delay > 0

    def test_rate_limit_precision(self, limiter):
        """Test precision of rate limiting delays."""
        # Use up burst capacity
        for _ in range(20):
            limiter.acquire()

        # Test subsequent requests
        start_time = time.monotonic()
        delays = []
        for _ in range(5):
            delay = limiter.acquire()
            delays.append(delay)

        # Verify delays are properly spaced
        for i in range(1, len(delays)):
            assert abs(delays[i] - delays[i - 1] - 0.1) < 0.01  # ~0.1s between requests

    def test_negative_time_handling(self, limiter):
        """Test handling of negative time differences."""
        with patch('time.monotonic') as mock_time:
            mock_time.side_effect = [1000.0, 999.9]  # Time going backwards

            limiter.acquire()  # Should handle this gracefully
            delay = limiter.acquire()

            assert delay >= 0  # Should never return negative delay
