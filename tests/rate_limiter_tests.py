"""Tests for the rate limiting functionality."""

import unittest
import time
from bcra_connector.rate_limiter import RateLimiter, RateLimitConfig


class TestRateLimiter(unittest.TestCase):
    """Test suite for the RateLimiter class."""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        config = RateLimitConfig(calls=3, period=1.0, burst=3)
        limiter = RateLimiter(config)

        # First 3 calls should be immediate
        for _ in range(3):
            delay = limiter.acquire()
            self.assertEqual(delay, 0)

        # Fourth call should be delayed
        start = time.monotonic()
        delay = limiter.acquire()
        elapsed = time.monotonic() - start
        self.assertGreater(delay, 0)
        self.assertGreater(elapsed, 0.9)  # Allow for small timing variations

    def test_burst_handling(self):
        """Test burst handling functionality."""
        config = RateLimitConfig(calls=2, period=1.0, burst=4)
        limiter = RateLimiter(config)

        # First 4 calls should be immediate (burst limit)
        for _ in range(4):
            delay = limiter.acquire()
            self.assertEqual(delay, 0)

        # Fifth call should be delayed
        delay = limiter.acquire()
        self.assertGreater(delay, 0)

    def test_reset(self):
        """Test reset functionality."""
        config = RateLimitConfig(calls=2, period=1.0)
        limiter = RateLimiter(config)

        # Use up the rate limit
        for _ in range(2):
            limiter.acquire()

        self.assertTrue(limiter.is_limited)
        limiter.reset()
        self.assertFalse(limiter.is_limited)

    def test_remaining_calls(self):
        """Test remaining calls calculation."""
        config = RateLimitConfig(calls=3, period=1.0)
        limiter = RateLimiter(config)

        self.assertEqual(limiter.remaining_calls(), 3)
        limiter.acquire()
        self.assertEqual(limiter.remaining_calls(), 2)
        limiter.acquire()
        self.assertEqual(limiter.remaining_calls(), 1)
        limiter.acquire()
        self.assertEqual(limiter.remaining_calls(), 0)

    def test_invalid_config(self):
        """Test invalid configuration handling."""
        with self.assertRaises(ValueError):
            RateLimitConfig(calls=0, period=1.0)
        
        with self.assertRaises(ValueError):
            RateLimitConfig(calls=1, period=0)
        
        with self.assertRaises(ValueError):
            RateLimitConfig(calls=2, period=1.0, burst=1)