# Performance Baseline (Initial)

Date: 2026-02-18

These numbers are local baseline measurements to compare future optimization work.

## Commands
- `python3 -m pytest -q`
- `python3 -m pytest -q tests/test_runtime_determinism.py`
- `python3 -m flavent check examples/minimal.flv --strict`

## Results
- Full test suite: `8.102s` wall time (`278 passed in 7.14s` reported by pytest).
- Runtime determinism tests: `0.557s` wall time (`5 passed in 0.16s` reported by pytest).
- Compiler check (minimal example): `0.208s` wall time.

## Notes
- Measurements include Python process startup overhead.
- Use these values as a relative baseline only (not cross-machine absolute targets).

---

# Performance Snapshot (Updated)

Date: 2026-02-18

Generated with:
- `python3 scripts/perf_snapshot.py`

## Benchmarks + Memory
- Full test suite: `9.674s` wall, `46420 KB` max RSS, summary: `295 passed in 8.69s`.
- Runtime determinism tests: `0.610s` wall, `31112 KB` max RSS, summary: `5 passed in 0.18s`.
- Compiler check (minimal, strict): `0.231s` wall, `18076 KB` max RSS, summary: `OK`.

## Delta vs Initial Baseline
- Full suite wall: `+1.572s` vs initial (`8.102s` → `9.674s`).
- Runtime determinism wall: `+0.053s` vs initial (`0.557s` → `0.610s`).
- Minimal strict check wall: `+0.023s` vs initial (`0.208s` → `0.231s`).
- Note: the full-suite delta includes additional tests added since the initial snapshot (`278` → `295` passed).

## cProfile Hotspots (per-module)
- Compiler pipeline (`examples/minimal.flv`, repeated):
  - `flavent/typecheck.py:107 check_program` (cum ~`1.47s`)
  - `flavent/typecheck.py:490 _check_fn` (cum ~`1.24s`)
  - `flavent/resolve.py:709 resolve_program_with_stdlib` (cum ~`0.72s`)
  - `flavent/resolve.py:981 _resolve_uses` (cum ~`0.51s`)
  - `flavent/resolve.py:1088 _resolve_fn` (cum ~`0.48s`)
- Runtime hot loop (`emit`/`await` ping-pong, repeated):
  - `flavent/runtime.py:69 run_hir_program` (cum ~`0.64s`)
  - `flavent/runtime.py:666 _advance_task` (cum ~`0.31s`)
  - `flavent/runtime.py:680 _gen` (cum ~`0.28s`)
  - `flavent/runtime.py:523 exec_block_gen` (cum ~`0.27s`)
  - `flavent/runtime.py:533 exec_stmt_gen` (cum ~`0.25s`)

---

# Post Runtime-Queue Optimization Snapshot

Date: 2026-02-18

Optimization focus:
- runtime queue path (`list.pop(0)` → `deque.popleft()`)
- event dispatch path (event-type heap + pre-indexed handlers)
- match-bind restore path (targeted bind/restore instead of full `dict(env)` copy)

Measured with:
- `python3 scripts/perf_snapshot.py`

## Benchmarks + Memory
- Full test suite: `10.086s` wall, `46192 KB` max RSS, summary: `295 passed in 8.98s`.
- Runtime determinism tests: `0.686s` wall, `31168 KB` max RSS, summary: `5 passed in 0.18s`.
- Compiler check (minimal, strict): `0.256s` wall, `17932 KB` max RSS, summary: `OK`.

## Runtime Hotspot Delta (cProfile, focused)
- `run_hir_program` cumulative: `~0.64s` → `~0.61s` (improved).
- `_advance_task` cumulative: `~0.31s` → `~0.30s` (improved).
- `exec_block_gen` cumulative: `~0.27s` → `~0.26s` (improved).
- Note: wall-clock suite benchmarks are noisy; cProfile hotspot reductions are the more stable signal for this pass.
