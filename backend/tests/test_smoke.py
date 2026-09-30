"""Smoke tests: the package imports and exposes a version."""

import app
import app.content_engine


def test_package_version() -> None:
    assert app.__version__ == "0.1.0"


def test_content_engine_importable() -> None:
    assert app.content_engine.__doc__
