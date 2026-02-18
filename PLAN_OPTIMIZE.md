# Language & Stdlib Optimization Plan

## Goal
Refine Flavent language behavior and standard library consistency while improving runtime performance and keeping backward compatibility.

## Principles
- Keep existing user programs working unless a change is explicitly marked and documented.
- Prefer additive improvements over breaking changes.
- Require test coverage for each semantic or stdlib behavior change.

## Phase 1: Baseline and Audit (Current)
- [x] Define initial benchmark scenarios for:
  - event loop scheduling (`emit`/`await` chains)
  - collection-heavy operations (`list`, `map`, `queue`)
  - parsing/checking representative examples
- [x] Capture first runtime baseline and store in `docs/perf_baseline.md`.
- [ ] Expand baseline with memory snapshots and per-module profiles.
- [x] Create stdlib API consistency checklist in `docs/stdlib_api_checklist.md`:
  - naming consistency (`camelCase` vs `snake_case` not mixed)
  - error style (`Result` vs sentinel values)
  - Option/Result ergonomics (`unwrapOr`, `isSome`, etc.)

## Phase 2: Language Semantics Refinement
- [ ] Tighten and document event semantics:
  - deterministic dispatch ordering
  - FIFO waiter wake-up ordering
  - constructor-based `emit` behavior
- [ ] Add regression tests for mixed event-type workloads and long-running chains.
- [ ] Align diagnostics for semantic errors (clear actionable messages).

## Phase 3: Stdlib API Refinement
- [~] Normalize module APIs with mismatched naming and edge-case behavior.
  - [x] Added `strStartsWith` / `strEndsWith` aliases in `stringlib`.
  - [x] Added Option-based find APIs: `strFindOpt` / `bytesFindOpt`.
  - [x] Added Option-based find helpers in `httplib/core`.
  - [ ] Continue with follow-up modules (`regex`, targeted stdlib edge cases).
- [ ] Add/expand tests for invalid input handling in stdlib modules.
- [ ] Update docs/examples to reflect final APIs.

## Phase 4: Performance Pass
- [ ] Optimize hot runtime paths identified in baseline.
- [ ] Re-run benchmarks and compare to baseline.
- [ ] Keep behavior unchanged unless documented in changelog/migration notes.

## Exit Criteria
- Full test suite green.
- No unresolved TODOs in this plan.
- Documented benchmark deltas and API refinements.
