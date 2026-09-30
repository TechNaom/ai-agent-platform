"""Provider adapter protocol. Every transport (Anthropic, OpenAI-compatible) implements this."""

from typing import Protocol

from app.content_engine.models.types import CallSpec, CompletionResult


class Provider(Protocol):
    name: str

    async def complete(self, *, model: str, spec: CallSpec) -> CompletionResult: ...
