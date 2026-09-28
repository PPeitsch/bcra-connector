"""Unit tests for the rate limiting functionality."""

import threading
from typing import List, Optional

import pytest

from bcra_connector.rate_limiter import RateLimitConfig, RateLimiter


class FakeClock:
    """A monotonic clock that only moves when told to."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    """Drive the limiter with a fake clock, so timing is exact and nothing sleeps."""
    fake = FakeClock()
    monkeypatch.setattr("bcra_connector.rate_limiter.monotonic", fake)
    return fake


def send_for(limiter: RateLimiter, clock: FakeClock, seconds: float) -> List[float]:
    """Send requests back to back, sleeping what acquire() asks, for ``seconds``.

    :return: The time each request went out
    """
    sent: List[float] = []
    while True:
        clock.sleep(limiter.acquire())
        if clock.now >= seconds:
            return sent
        sent.append(clock.now)


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
    def limiter(self, clock: FakeClock) -> RateLimiter:
        """Create a RateLimiter with a burst above its rate, on the fake clock."""
        return RateLimiter(RateLimitConfig(calls=10, period=1.0, _burst=20))

    def test_burst_goes_out_without_waiting(self, limiter: RateLimiter) -> None:
        """The first ``burst`` calls don't wait; the next one waits one token."""
        for _ in range(limiter.config.burst):
            assert limiter.acquire() == 0

        assert limiter.acquire() == pytest.approx(0.1)

    @pytest.mark.parametrize(
        "calls,period,burst",
        [
            (2, 1.0, 4),  # measured at ~5 req/s before #170
            (4, 1.0, None),
            (1, 2.0, 3),
        ],
    )
    def test_sustained_rate_is_calls_per_period(
        self, clock: FakeClock, calls: int, period: float, burst: Optional[int]
    ) -> None:
        """After the burst, every period lets through ``calls``, not ``burst``."""
        limiter = RateLimiter(RateLimitConfig(calls=calls, period=period, _burst=burst))
        periods = 10

        sent = send_for(limiter, clock, periods * period)

        per_period = [
            sum(1 for t in sent if k * period <= t < (k + 1) * period)
            for k in range(periods)
        ]
        assert per_period[0] == limiter.config.burst + calls - 1
        assert per_period[1:] == [calls] * (periods - 1)

    def test_idle_refills_up_to_burst(
        self, limiter: RateLimiter, clock: FakeClock
    ) -> None:
        """A long pause earns back the burst, and no more."""
        send_for(limiter, clock, 3.0)

        clock.sleep(60.0)

        for _ in range(limiter.config.burst):
            assert limiter.acquire() == 0
        assert limiter.acquire() > 0

    def test_partial_refill(self, limiter: RateLimiter, clock: FakeClock) -> None:
        """Half a period earns half the calls."""
        for _ in range(limiter.config.burst):
            limiter.acquire()

        clock.sleep(0.5)

        for _ in range(5):
            assert limiter.acquire() == 0
        assert limiter.acquire() == pytest.approx(0.1)

    def test_concurrent_callers_line_up(self, limiter: RateLimiter) -> None:
        """Callers past the burst each wait one token longer than the previous."""
        extra = 5
        delays: List[float] = []
        delays_lock = threading.Lock()

        def worker() -> None:
            delay = limiter.acquire()
            with delays_lock:
                delays.append(delay)

        threads = [
            threading.Thread(target=worker) for _ in range(limiter.config.burst + extra)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        delays.sort()
        assert delays[: limiter.config.burst] == [0.0] * limiter.config.burst
        assert delays[limiter.config.burst :] == pytest.approx(
            [0.1 * (i + 1) for i in range(extra)]
        )

    def test_reset(self, limiter: RateLimiter) -> None:
        """Reset fills the bucket back up."""
        for _ in range(25):
            limiter.acquire()

        limiter.reset()

        assert limiter.current_usage == 0
        assert limiter.remaining_calls() == limiter.config.burst
        assert limiter.acquire() == 0

    def test_current_usage(self, limiter: RateLimiter, clock: FakeClock) -> None:
        """Usage counts taken tokens, including waiting calls, and decays with time."""
        assert limiter.current_usage == 0

        for _ in range(22):
            limiter.acquire()
        assert limiter.current_usage == 22

        clock.sleep(1.0)
        assert limiter.current_usage == 12

    def test_remaining_calls(self, limiter: RateLimiter, clock: FakeClock) -> None:
        """Remaining calls are the ones that can go out now, up to the burst."""
        assert limiter.remaining_calls() == 20

        limiter.acquire()
        assert limiter.remaining_calls() == 19

        for _ in range(21):
            limiter.acquire()
        assert limiter.remaining_calls() == 0

        clock.sleep(0.45)
        assert limiter.remaining_calls() == 2

    def test_is_limited(self, limiter: RateLimiter, clock: FakeClock) -> None:
        """Limited while the next call would wait."""
        assert not limiter.is_limited

        for _ in range(20):
            limiter.acquire()
        assert limiter.is_limited

        clock.sleep(0.1)
        assert not limiter.is_limited


def test_real_clock_smoke() -> None:
    """On the real clock, the call past the burst waits about one token."""
    limiter = RateLimiter(RateLimitConfig(calls=10, period=1.0))

    for _ in range(10):
        assert limiter.acquire() == 0

    assert 0.05 < limiter.acquire() <= 0.1
