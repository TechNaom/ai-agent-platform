"""Circuit breaker opens after repeated failures and half-opens after cooldown."""

from app.worker.breaker import CircuitBreaker
from app.worker.registry import Registry, breaker_key


def test_opens_after_threshold_and_half_opens() -> None:
    b = CircuitBreaker(failure_threshold=2, cooldown_seconds=10)
    b.record_failure("news.rss", now=0)
    assert not b.is_open("news.rss", now=1)
    b.record_failure("news.rss", now=1)
    assert b.is_open("news.rss", now=5)
    assert not b.is_open("news.rss", now=12)  # half-open trial allowed
    b.record_failure("news.rss", now=12)  # trial failed: re-open immediately
    assert b.is_open("news.rss", now=13)


def test_success_resets() -> None:
    b = CircuitBreaker(failure_threshold=1)
    b.record_failure("k", now=0)
    b.record_success("k")
    assert not b.is_open("k", now=0)


def test_breaker_key_groups_by_family() -> None:
    assert breaker_key("publish.linkedin.post") == "publish.linkedin"
    assert breaker_key("scan") == "scan"


def test_registry_rejects_duplicates() -> None:
    reg = Registry()

    @reg.register("a")
    async def a(_ctx: object) -> None: ...

    try:
        reg.register("a")(a)
    except ValueError:
        return
    raise AssertionError("duplicate registration should fail")
