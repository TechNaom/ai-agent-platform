"""Anthropic transport. Converts the provider-neutral CallSpec to/from the Claude API."""

from typing import Any, cast

from anthropic import APIStatusError, AsyncAnthropic, RateLimitError

from app.content_engine.models.errors import ProviderError
from app.content_engine.models.types import CallSpec, CompletionResult, Role, ToolCall


def _to_anthropic_messages(spec: CallSpec) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in spec.messages:
        if m.role == Role.TOOL:
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.tool_call_id,
                            "content": m.content,
                        }
                    ],
                }
            )
        elif m.role == Role.ASSISTANT and m.tool_calls:
            blocks: list[dict[str, Any]] = []
            if m.content:
                blocks.append({"type": "text", "text": m.content})
            blocks += [
                {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments}
                for tc in m.tool_calls
            ]
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": m.role.value, "content": m.content})
    return out


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, client: AsyncAnthropic) -> None:
        self._client = client

    async def complete(self, *, model: str, spec: CallSpec) -> CompletionResult:
        tools = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in spec.tools
        ]
        try:
            # `temperature` is intentionally omitted: current Claude models use adaptive
            # thinking, not manual sampling temperature (see docs/ARCHITECTURE.md).
            resp = await self._client.messages.create(
                model=model,
                system=spec.system or "",
                messages=cast(Any, _to_anthropic_messages(spec)),
                tools=cast(Any, tools),
                max_tokens=spec.max_tokens,
            )
        except RateLimitError as exc:
            raise ProviderError(self.name, model, str(exc), retryable=True) from exc
        except APIStatusError as exc:
            retryable = exc.status_code >= 500
            raise ProviderError(self.name, model, str(exc), retryable=retryable) from exc

        text = "".join(b.text for b in resp.content if b.type == "text")
        tool_calls = tuple(
            ToolCall(id=b.id, name=b.name, arguments=dict(b.input))
            for b in resp.content
            if b.type == "tool_use"
        )
        return CompletionResult(
            text=text,
            tool_calls=tool_calls,
            tokens_in=resp.usage.input_tokens,
            tokens_out=resp.usage.output_tokens,
            stop_reason=resp.stop_reason or "unknown",
            raw_model=resp.model,
        )
