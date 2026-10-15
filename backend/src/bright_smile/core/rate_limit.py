"""In-memory sliding-window rate limiting (SPEC section 10.2).

State lives in the process, which is correct for the single backend instance v1 runs on. A
multi-instance deployment would move this to a shared store.
"""

import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum


class Policy(StrEnum):
    CHAT = "chat"
    LEAD_FORM = "lead_form"
    LOGIN = "login"


@dataclass(frozen=True)
class RateLimit:
    limit: int
    window: timedelta


POLICIES: dict[Policy, RateLimit] = {
    Policy.CHAT: RateLimit(limit=20, window=timedelta(minutes=1)),
    Policy.LEAD_FORM: RateLimit(limit=5, window=timedelta(hours=1)),
    Policy.LOGIN: RateLimit(limit=5, window=timedelta(minutes=15)),
}


@dataclass
class RateLimiter:
    """Sliding window per (policy, client key). Not thread-safe; used from the event loop only."""

    policies: dict[Policy, RateLimit] = field(default_factory=lambda: dict(POLICIES))
    clock: Callable[[], float] = time.monotonic
    _hits: dict[tuple[Policy, str], deque[float]] = field(default_factory=dict)

    def hit(self, policy: Policy, key: str) -> int | None:
        """Record a request. Returns None if allowed, else seconds until the next slot frees up."""
        rule = self.policies[policy]
        now = self.clock()
        window = rule.window.total_seconds()
        hits = self._hits.setdefault((policy, key), deque())
        while hits and hits[0] <= now - window:
            hits.popleft()
        if len(hits) >= rule.limit:
            return max(1, math.ceil(hits[0] + window - now))
        hits.append(now)
        return None

    def reset(self) -> None:
        self._hits.clear()
