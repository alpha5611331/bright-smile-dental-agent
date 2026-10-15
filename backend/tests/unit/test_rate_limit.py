from datetime import timedelta

from bright_smile.core.rate_limit import POLICIES, Policy, RateLimit, RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make_limiter(clock: FakeClock) -> RateLimiter:
    return RateLimiter(policies={Policy.LOGIN: RateLimit(3, timedelta(seconds=60))}, clock=clock)


def test_allows_up_to_the_limit_then_reports_retry_after() -> None:
    clock = FakeClock()
    limiter = make_limiter(clock)

    assert [limiter.hit(Policy.LOGIN, "1.2.3.4") for _ in range(3)] == [None, None, None]
    clock.now += 15
    assert limiter.hit(Policy.LOGIN, "1.2.3.4") == 45


def test_window_slides() -> None:
    clock = FakeClock()
    limiter = make_limiter(clock)
    for _ in range(3):
        limiter.hit(Policy.LOGIN, "1.2.3.4")

    clock.now += 60

    assert limiter.hit(Policy.LOGIN, "1.2.3.4") is None


def test_clients_and_policies_are_independent() -> None:
    limiter = RateLimiter(clock=FakeClock())
    for _ in range(5):
        limiter.hit(Policy.LOGIN, "1.2.3.4")

    assert limiter.hit(Policy.LOGIN, "5.6.7.8") is None
    assert limiter.hit(Policy.CHAT, "1.2.3.4") is None


def test_reset_clears_all_windows() -> None:
    clock = FakeClock()
    limiter = make_limiter(clock)
    for _ in range(3):
        limiter.hit(Policy.LOGIN, "1.2.3.4")

    limiter.reset()

    assert limiter.hit(Policy.LOGIN, "1.2.3.4") is None


def test_spec_policies() -> None:
    assert POLICIES[Policy.CHAT] == RateLimit(20, timedelta(minutes=1))
    assert POLICIES[Policy.LEAD_FORM] == RateLimit(5, timedelta(hours=1))
    assert POLICIES[Policy.LOGIN] == RateLimit(5, timedelta(minutes=15))
