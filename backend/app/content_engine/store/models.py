"""Content engine schema: the single shared memory for all agents (ADR-0002).

Plan: docs/content-engine/ARCHITECTURE_PLAN.md §5 · Memory: docs/content-engine/AGENT_MEMORY.md
"""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# One embedding size for all semantic memory. 1024 fits common embedding models
# (e.g. Voyage, bge-m3, Cohere). Changing it requires a migration + re-embedding.
EMBEDDING_DIM = 1024


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSONB, list[Any]: JSONB}


def enum_col(enum: type[StrEnum]) -> Enum:
    """Store enums as VARCHAR (portable, easy to extend), validated in Python."""
    return Enum(
        enum,
        native_enum=False,
        length=32,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


def created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def updated_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------- enums


class SourceKind(StrEnum):
    GITHUB_REPO = "github_repo"
    NEWS_FEED = "news_feed"


class SourceStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    EXCLUDED = "excluded"


class NodeKind(StrEnum):
    REPO = "repo"
    CHAPTER = "chapter"
    CONCEPT = "concept"


class NewsTier(StrEnum):
    NORMAL = "normal"
    IMPORTANT = "important"
    HIGH = "high"
    BREAKING = "breaking"


class Pillar(StrEnum):
    """Brand pillars (plan §0). Every opportunity maps to exactly one."""

    BUILDING_AI_SYSTEMS = "building_ai_systems"
    AI_IN_PRODUCTION = "ai_in_production"
    AI_NEWS_PRACTITIONER = "ai_news_practitioner"
    AI_ENABLEMENT = "ai_enablement"
    TEACHING_AI = "teaching_ai"


class ContentFormat(StrEnum):
    TEXT = "text"
    CAROUSEL = "carousel"
    THREAD = "thread"
    ARTICLE = "article"


class Lifecycle(StrEnum):
    """Content lifecycle (plan §5 / PRD §26)."""

    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    DECOMPOSED = "decomposed"
    GENERATED = "generated"
    VALIDATED = "validated"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    MEASURED = "measured"
    ARCHIVED = "archived"
    RECYCLABLE = "recyclable"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class Channel(StrEnum):
    LINKEDIN = "linkedin"
    X = "x"
    BLUESKY = "bluesky"
    THREADS = "threads"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    BLOG = "blog"
    DEVTO = "devto"
    HASHNODE = "hashnode"
    NEWSLETTER = "newsletter"


class ClaimType(StrEnum):
    CONFIRMED = "confirmed"
    ANNOUNCED = "announced"
    REPORTED = "reported"
    SPECULATION = "speculation"


class ClaimVerdict(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    SPECULATION_LABELLED = "speculation_labelled"


class SlotKind(StrEnum):
    MORNING = "morning"
    EVENING = "evening"
    BREAKING = "breaking"
    EXTRA = "extra"


class SlotState(StrEnum):
    OPEN = "open"
    FILLED = "filled"
    PUBLISHED = "published"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class PublishMode(StrEnum):
    SHADOW = "shadow"
    VETO = "veto"
    AUTONOMOUS = "autonomous"


class PublicationStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class MetricsSource(StrEnum):
    API = "api"
    CSV = "csv"


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class LessonStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    RETIRED = "retired"


# ---------------------------------------------------------------- sources & knowledge


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[SourceKind] = mapped_column(enum_col(SourceKind))
    name: Mapped[str] = mapped_column(String(200), unique=True)
    url: Mapped[str] = mapped_column(Text)
    config: Mapped[dict[str, Any]] = mapped_column(default=dict)
    credibility: Mapped[float | None] = mapped_column(Float)
    status: Mapped[SourceStatus] = mapped_column(
        enum_col(SourceStatus), default=SourceStatus.ACTIVE
    )
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_commit_sha: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()


class SourceDocument(Base):
    __tablename__ = "source_documents"
    __table_args__ = (UniqueConstraint("source_id", "path"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    path: Mapped[str] = mapped_column(Text)
    blob_sha: Mapped[str] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    updated_at: Mapped[datetime] = updated_at()


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_nodes.id"))
    kind: Mapped[NodeKind] = mapped_column(enum_col(NodeKind))
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    doc_refs: Mapped[list[Any]] = mapped_column(default=list)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = created_at()


# ---------------------------------------------------------------- news


class NewsEvent(Base):
    __tablename__ = "news_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    tier: Mapped[NewsTier] = mapped_column(enum_col(NewsTier), default=NewsTier.NORMAL)
    scores: Mapped[dict[str, Any]] = mapped_column(default=dict)
    corroboration_count: Mapped[int] = mapped_column(Integer, default=0)
    primary_url: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = created_at()
    status: Mapped[Lifecycle] = mapped_column(enum_col(Lifecycle), default=Lifecycle.DISCOVERED)


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"))
    url: Mapped[str] = mapped_column(Text, unique=True)
    headline: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excerpt: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    collected_at: Mapped[datetime] = created_at()


# ---------------------------------------------------------------- content


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("agent", "version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32))
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = created_at()


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    knowledge_node_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_nodes.id"))
    news_event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"))
    pillar: Mapped[Pillar] = mapped_column(enum_col(Pillar))
    angle: Mapped[str] = mapped_column(Text)
    format: Mapped[ContentFormat] = mapped_column(enum_col(ContentFormat))
    content_type: Mapped[str] = mapped_column(String(64))
    audience: Mapped[str | None] = mapped_column(Text)
    evidence_refs: Mapped[list[Any]] = mapped_column(default=list)
    series_key: Mapped[str | None] = mapped_column(String(128))
    priority: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[Lifecycle] = mapped_column(
        enum_col(Lifecycle), default=Lifecycle.DISCOVERED, index=True
    )
    reject_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()


class Draft(Base):
    """Canonical post (one per opportunity version); channel variants derive from it."""

    __tablename__ = "drafts"
    __table_args__ = (UniqueConstraint("opportunity_id", "version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    body: Mapped[str] = mapped_column(Text)
    hook_type: Mapped[str | None] = mapped_column(String(64))
    format: Mapped[ContentFormat] = mapped_column(enum_col(ContentFormat))
    char_count: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    prompt_version_id: Mapped[int | None] = mapped_column(ForeignKey("prompt_versions.id"))
    model: Mapped[str | None] = mapped_column(String(128))
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[Lifecycle] = mapped_column(enum_col(Lifecycle), default=Lifecycle.GENERATED)
    created_at: Mapped[datetime] = created_at()


class ChannelVariant(Base):
    __tablename__ = "channel_variants"
    __table_args__ = (UniqueConstraint("draft_id", "channel"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    channel: Mapped[Channel] = mapped_column(enum_col(Channel))
    body: Mapped[str] = mapped_column(Text)
    media: Mapped[list[Any]] = mapped_column(default=list)
    status: Mapped[Lifecycle] = mapped_column(enum_col(Lifecycle), default=Lifecycle.GENERATED)
    created_at: Mapped[datetime] = created_at()


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[ClaimType] = mapped_column(enum_col(ClaimType))
    evidence_url: Mapped[str | None] = mapped_column(Text)
    evidence_span: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[ClaimVerdict] = mapped_column(enum_col(ClaimVerdict))


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"))
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("channel_variants.id", ondelete="CASCADE")
    )
    rubric: Mapped[dict[str, Any]] = mapped_column(default=dict)
    overall: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    reasons: Mapped[list[Any]] = mapped_column(default=list)
    judge_model: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = created_at()


# ---------------------------------------------------------------- scheduling & publishing


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"
    __table_args__ = (UniqueConstraint("channel", "scheduled_for"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel: Mapped[Channel] = mapped_column(enum_col(Channel))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kind: Mapped[SlotKind] = mapped_column(enum_col(SlotKind))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("channel_variants.id"))
    replaced_variant_id: Mapped[int | None] = mapped_column(ForeignKey("channel_variants.id"))
    state: Mapped[SlotState] = mapped_column(enum_col(SlotState), default=SlotState.OPEN)
    skip_reason: Mapped[str | None] = mapped_column(Text)


class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("schedule_slots.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("channel_variants.id"))
    channel: Mapped[Channel] = mapped_column(enum_col(Channel))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    external_id: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[PublishMode] = mapped_column(enum_col(PublishMode))
    status: Mapped[PublicationStatus] = mapped_column(
        enum_col(PublicationStatus), default=PublicationStatus.PENDING
    )
    error: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at()


class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), index=True
    )
    taken_at: Mapped[datetime] = created_at()
    source: Mapped[MetricsSource] = mapped_column(enum_col(MetricsSource))
    impressions: Mapped[int | None] = mapped_column(Integer)
    members_reached: Mapped[int | None] = mapped_column(Integer)
    reactions: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    reshares: Mapped[int | None] = mapped_column(Integer)
    saves: Mapped[int | None] = mapped_column(Integer)
    sends: Mapped[int | None] = mapped_column(Integer)
    link_clicks: Mapped[int | None] = mapped_column(Integer)
    # Brand metrics (CHANNEL_SPIKE.md): the learning loop's primary signals.
    followers_gained: Mapped[int | None] = mapped_column(Integer)
    profile_views: Mapped[int | None] = mapped_column(Integer)


class TopicHistory(Base):
    __tablename__ = "topic_history"

    topic_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    last_published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cooldown_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    count: Mapped[int] = mapped_column(Integer, default=1)


# ---------------------------------------------------------------- operations & learning


class Job(Base):
    """Durable job queue (ADR-0004). Claimed with SELECT … FOR UPDATE SKIP LOCKED."""

    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_state_run_after", "state", "run_after"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(default=dict)
    state: Mapped[JobState] = mapped_column(enum_col(JobState), default=JobState.QUEUED)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(String(128))
    last_error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pipeline: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[RunStatus] = mapped_column(enum_col(RunStatus), default=RunStatus.RUNNING)
    started_at: Mapped[datetime] = created_at()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal(0))
    tokens_in: Mapped[int] = mapped_column(BigInteger, default=0)
    tokens_out: Mapped[int] = mapped_column(BigInteger, default=0)
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(128))
    error: Mapped[str | None] = mapped_column(Text)


class Lesson(Base):
    """Procedural memory (AGENT_MEMORY.md layer 5); active only after an eval gate."""

    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scope: Mapped[str] = mapped_column(String(32))
    statement: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(default=dict)
    proposed_by: Mapped[str] = mapped_column(String(64))
    status: Mapped[LessonStatus] = mapped_column(
        enum_col(LessonStatus), default=LessonStatus.PROPOSED
    )
    eval_run_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = created_at()
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Setting(Base):
    """Runtime switches: mode, kill_switch, caps, slot times, mix targets."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column()
    updated_at: Mapped[datetime] = updated_at()
