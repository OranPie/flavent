# Grammar & Structure Improvement Plan

## Goal
Improve language grammar clarity and compiler structure while reducing runtime dependence on Python bridge primitives (`_bridge_python`).

## Guiding Principles
- Keep backward compatibility for existing `.flv` programs.
- Prefer additive grammar improvements with clear diagnostics.
- Replace bridge-backed behavior with pure Flavent implementations where practical.
- Ship each step with tests and measurable bridge-usage reduction.

## Phase 1: Baseline and Inventory
- [x] Capture current bridge surface:
  - [x] list all stdlib bridge primitives used in `stdlib/_bridge_python.flv`
  - [x] map which stdlib modules consume each primitive
- [x] Add baseline metrics:
  - [x] count of bridge calls in runtime tests
  - [x] count of bridge symbols referenced by stdlib
- Notes:
  - Baseline tooling: `scripts/bridge_usage_snapshot.py`
  - Current snapshot: `docs/bridge_usage_baseline.md` + `docs/bridge_usage_baseline.json`
- [x] Document current grammar pain points (escapes, precedence edge cases, pattern/match ergonomics).
  - Baseline doc: `docs/grammar_pain_points.md`

## Phase 2: Grammar Refinement
- [ ] Publish a compact EBNF-style grammar supplement in docs.
- [ ] Tighten literal grammar and diagnostics (invalid escapes, malformed bytes/hex, recoverable parser errors).
- [ ] Add parser/lexer regression tests for ambiguous and edge-case constructs.
- [ ] Improve user-facing error messages with expected-token hints.

## Phase 3: Compiler Structure Improvements
- [ ] Split parser/lexer helper logic into clearer internal units (without public API breakage).
- [ ] Reduce duplicated control-flow in runtime interpreter hot paths.
- [ ] Add internal invariants/assertions for resolved AST/HIR assumptions.

## Phase 4: Reduce Python Bridge Dependency
Priority order:
1. String/bytes helpers that can be pure-Flavent.
2. Deterministic collection and utility operations.
3. Keep only unavoidable host-integration primitives (IO/network/OS).

Tasks:
- [ ] Introduce pure-Flavent replacements module-by-module.
- [ ] Keep bridge fallbacks only where host access is required.
- [ ] Add CI check/report for bridge-usage trend (target downward each release).

## Exit Criteria
- [ ] Full test suite green.
- [ ] Bridge symbol usage reduced by a measurable, documented percentage.
- [ ] Grammar supplement + migration notes published.
