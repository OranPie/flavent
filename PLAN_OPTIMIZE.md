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
- [x] Expand baseline with memory snapshots and per-module profiles (see `scripts/perf_snapshot.py` and updated `docs/perf_baseline.md`).
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
  - [x] Completed `regex` edge-case pass:
    - fixed zero-length `replaceAll` termination behavior
    - fixed capture propagation for grouped matches in `replace`/`findFirstCaptures`
    - added runtime and `.flv` tests for anchors, compile errors, zero-length, and replacement tokens
- [~] Add/expand tests for invalid input handling in stdlib modules.
  - [x] `regex`: compile errors, anchor edge cases, zero-length replacement behavior.
  - [x] `struct`: format/value/buffer error paths (`too many values`, `not enough values`, `unsupported format`, `dangling count`, short buffer).
- [x] Update docs/examples to reflect final APIs (`regex`, `stringlib`, `bytelib`, `httplib.core` in `docs/en` + `docs/zh`).

## Phase 4: Performance Pass
- [~] Optimize hot runtime paths identified in baseline.
  - [x] Runtime event-loop queue structures optimized:
    - switched runnable/event/waiter FIFO queues from `list.pop(0)` to `deque.popleft()`
    - added min-heap dispatch for event type scheduling and pre-indexed handlers by event type
  - [x] Reduced environment-copy overhead in pattern matching:
    - replaced full `dict(env)` snapshot in `match` paths with targeted bind/restore of bound symbols only
- [x] Re-run benchmarks and compare to baseline (documented in `docs/perf_baseline.md`).
- [ ] Keep behavior unchanged unless documented in changelog/migration notes.

## Exit Criteria
- Full test suite green.
- No unresolved TODOs in this plan.
- Documented benchmark deltas and API refinements.
