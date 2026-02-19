# Stdlib Expansion Plan

## Goal
Expand Flavent stdlib with consistent APIs, fewer duplicated helpers, and stronger docs/tests coverage.

## Principles
- Keep compatibility first: additive APIs before removals.
- Prefer shared helper modules over copy-paste logic.
- Every new module/API must ship with docs + tests.
- Track bridge usage and keep deterministic helpers pure-Flavent where possible.

## Phase 0: Current Baseline
- [x] Add cross-module duplicate detector: `scripts/stdlib_duplicate_defs.py`
- [x] Publish duplicate report artifact: `docs/stdlib_duplicate_defs.md`
- [x] Unify `httplib.core` helper usage through `stringlib` / `bytelib` / `asciilib`
- [x] Decouple `flvrepr` from direct `_bridge_python` use

## Phase 1: API Unification & Cleanup
- [x] Resolve remaining duplicate public APIs (`file` vs `fslib`, bridge wrappers in `time`)
- [x] Define canonical module ownership table (which module is source of truth per capability)
- [x] Mark duplicate APIs as wrappers/aliases in docs with migration notes
- [x] Add CI check that fails on unapproved new duplicate public defs

## Phase 2: Core Utility Expansion
- [x] Add `url` module (encode/decode/query parsing utilities)
- [x] Add `csv` module (read/write rows, delimiter/quote support)
- [x] Add `path` module (join/base/ext/normalize helpers)
- [x] Add `datetime` module (parse/format ISO-like helpers)
- [x] Add `collections.deque` module for explicit queue/deque operations

## Phase 3: System & Runtime Expansion
- [x] Add `env` module (get/set/list env vars with `Result`)
- [x] Add `process` module (spawn/run/wait wrappers, structured errors)
- [x] Add `cliargs` module (argument parsing helpers for apps/tools)
- [x] Add `log` module (leveled logging helpers over `consoleIO`)

## Phase 4: Quality Gates Per Module
- [x] EN docs page in `docs/en/stdlib/*.md`
- [x] ZH docs page in `docs/zh/stdlib/*.md`
- [x] Python tests under `tests/test_stdlib_*.py`
- [x] Behavior tests under `tests_flv/test_stdlib_*.flv`
- [x] Add release note entry with compatibility notes

## Phase 5: Bridge-Reduction Track
- [x] Snapshot bridge usage after each batch (`scripts/bridge_usage_snapshot.py`)
- [x] Consolidate low-level string bridge usage through `stringlib` wrappers (`strLength`/`strCode`/`strSliceRange`/`strFromCodePoint`)
- [x] Migrate parser-heavy modules (`regex`, `httplib.core`, `struct`) to `stringlib` wrappers to remove direct `_bridge_python` imports
- [x] Migrate `json`/`hashlib.sha256`/`py` string handling to shared stdlib wrappers
- [x] Migrate additional utility modules (`process`, `file.lines`, `glob`, `uuid`, `base64.core`, `asciilib`, `stringfmt`) to shared string wrappers
- [ ] Prioritize replacing deterministic bridge-backed helpers with pure-Flavent versions
- [ ] Keep bridge-only functionality limited to IO/network/OS boundaries

## Exit Criteria
- [x] New modules documented in EN/ZH indexes
- [x] Full suite green (`python3 -m pytest -q tests tests_flv`)
- [x] Duplicate report trend non-increasing for public symbols
- [x] Bridge usage trend documented release-to-release
