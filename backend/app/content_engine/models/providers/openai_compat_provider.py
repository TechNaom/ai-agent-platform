"""OpenAI-compatible transport: works for Groq, OpenRouter, xAI by swapping base_url/model
(ADR-0003). Every non-Anthropic route in this platform goes through this one adapter.
"""

import json
from typing import Any, cast

from openai import APIStatusError, AsyncOpenAI, RateLimitError
from openai.types.chat import ChatCompletionMessageFunctionToolCall

from app.content_engine.models.errors import ProviderError
from app.content_engine.models.types import CallSpec, CompletionResult, Role, ToolCall


def _to_openai_messages(spec: CallSpec) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if spec.system:
        out.append({"role": "system", "content": spec.system})
    for m in spec.messages:
        if m.role == Role.TOOL:
            out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
        elif m.role == Role.ASSISTANT and m.tool_calls:
            out.append(
                {
                    "role": "assistant",
                    "content": m.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                        }
                        for tc in m.tool_calls
                    ],
                }
            )
        else:
            out.append({"role": m.role.value, "content": m.content})
    return out


class OpenAICompatProvider:
    def __init__(self, client: AsyncOpenAI, *, name: str) -> None:
        self._client = client
        self.name = name

    async def complete(self, *, model: str, spec: CallSpec) -> CompletionResult:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in spec.tools
        ]
        try:
            resp = await self._client.chat.completions.create(
                model=model,
                messages=cast(Any, _to_openai_messages(spec)),
                tools=cast(Any, tools or None),
                max_tokens=spec.max_tokens,
                temperature=spec.temperature,
            )
        except RateLimitError as exc:
            raise ProviderError(self.name, model, str(exc), retryable=True) from exc
        except APIStatusError as exc:
            retryable = exc.status_code >= 500
            raise ProviderError(self.name, model, str(exc), retryable=retryable) from exc

        choice = resp.choices[0]
        # Only function-tool calls are ever requested (see the `tools` payload above);
        # narrow the union so mypy (and we) can rely on `.function` existing.
        tool_calls = tuple(
            ToolCall(id=tc.id, name=tc.function.name, arguments=json.loads(tc.function.arguments))
            for tc in (choice.message.tool_calls or [])
            if isinstance(tc, ChatCompletionMessageFunctionToolCall)
        )
        usage = resp.usage
        return CompletionResult(
            text=choice.message.content or "",
            tool_calls=tool_calls,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            stop_reason=choice.finish_reason or "unknown",
            raw_model=resp.model,
        )
