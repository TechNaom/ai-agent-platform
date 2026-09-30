"""JSON log formatter includes the correlation ID when set."""

import json
import logging

from app.core.logging import JsonFormatter, correlation_id


def test_json_log_includes_correlation_id() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello", None, None)
    token = correlation_id.set("run-42")
    try:
        payload = json.loads(JsonFormatter().format(record))
    finally:
        correlation_id.reset(token)
    assert payload["msg"] == "hello"
    assert payload["correlation_id"] == "run-42"
