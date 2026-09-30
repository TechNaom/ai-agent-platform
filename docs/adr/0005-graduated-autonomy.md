# ADR-0005: Graduated autonomy: SHADOW → VETO → AUTONOMOUS

- Status: Accepted · 2026-09-30

## Context
The end state is fully automated publishing under the owner's name. The quality gates
must be proven before they are trusted with a real brand.

## Decision
A single `mode` setting. **SHADOW** publishes to a daily digest only. **VETO**
publishes unless the owner vetoes within a window. **AUTONOMOUS** is the target.
Promotion follows the measured criteria in the plan (§11), and any factual error found
in production automatically demotes to VETO. The kill switch overrides all modes.

## Consequences
No daily manual work in any mode. Autonomy is earned with evidence, not assumed.
