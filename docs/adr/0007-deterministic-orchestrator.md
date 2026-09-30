# ADR-0007: Deterministic orchestrator; LLM agents only for judgment

- Status: Accepted · 2026-09-30

## Context
The PRD lists about 12 "agents", including scheduler, publisher and dedup. An LLM making
scheduling or publishing decisions is non-deterministic, hard to test, and costly.

## Decision
The orchestrator, scheduler, editorial rules, dedup, publishers and analytics collection
are plain code. Ten LLM agents handle judgment: Repo Knowledge Mapper, Content
Strategist, News Scout & Analyst, Writer, Carousel Designer, Channel Adapter,
Fact-Checker, Brand & Quality Judge, Visual QA and Engagement Analyst.

## Consequences
Predictable, unit-testable control flow. LLM spend goes only where judgment adds value.
