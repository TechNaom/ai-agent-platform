"""Provider-neutral message/tool/result types (ADR-0003). No vendor SDK types leak past here."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    tool_call_id: str | None = None  # set on Role.TOOL: which call this answers
    tool_calls: tuple[ToolCall, ...] = ()  # set on Role.ASSISTANT when the model called tools


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the arguments object


@dataclass(frozen=True)
class CompletionResult:
    """What a provider returns for one call, before cost is attached."""

    text: str
    tool_calls: tuple[ToolCall, ...]
    tokens_in: int
    tokens_out: int
    stop_reason: str
    raw_model: str  # the model id actually used, as the provider reports it


@dataclass(frozen=True)
class ModelChoice:
    provider: str  # key into the router's provider registry, e.g. "anthropic", "groq"
    model: str


@dataclass(frozen=True)
class RoutedResult:
    """A CompletionResult plus routing/cost metadata, ready to persist to `runs`."""

    completion: CompletionResult
    choice: ModelChoice
    cost_usd: float
    attempt: int  # 1-indexed position in the fallback chain that succeeded


@dataclass(frozen=True)
class CallSpec:
    system: str | None
    messages: tuple[Message, ...]
    tools: tuple[ToolSpec, ...] = ()
    max_tokens: int = 1024
    temperature: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)
