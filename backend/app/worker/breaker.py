"""In-process circuit breaker per source family (plan §4.1: one source down ≠ system down)."""

import time
from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: float = 900.0
    _failures: dict[str, int] = field(default_factory=dict)
    _opened_at: dict[str, float] = field(default_factory=dict)

    def is_open(self, key: str, now: float | None = None) -> bool:
        opened = self._opened_at.get(key)
        if opened is None:
            return False
        if (now if now is not None else time.monotonic()) - opened >= self.cooldown_seconds:
            # Half-open: allow a trial call; the next result closes or re-opens it.
            del self._opened_at[key]
            self._failures[key] = self.failure_threshold - 1
            return False
        return True

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)
        self._opened_at.pop(key, None)

    def record_failure(self, key: str, now: float | None = None) -> None:
        self._failures[key] = self._failures.get(key, 0) + 1
        if self._failures[key] >= self.failure_threshold:
            self._opened_at[key] = now if now is not None else time.monotonic()
