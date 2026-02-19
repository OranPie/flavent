# Stdlib API Consistency Checklist (Phase 1)

Date: 2026-02-18

This checklist defines the first-pass refinement targets for stdlib API consistency.

## 1) Naming and Surface Conventions
- [x] Public function names use `camelCase` (no public `snake_case` functions found).
- [x] Prefix consistency per domain (first pass):
  - `stringlib`: `strFind`/`strContains` vs `startsWith`/`endsWith` (mixed style).
  - Added additive aliases `strStartsWith` / `strEndsWith` (kept existing names for compatibility).
- [ ] Internal helper visibility:
  - Ensure helper functions remain `_private` in modules where intended.

## 2) Error Channel Consistency
- [x] Sentinel-return APIs review:
  - `stdlib/stringlib/__init__.flv`: `strFind(...) -> Int` (uses `-1` not-found semantics through helper path).
  - `stdlib/bytelib/__init__.flv`: `bytesFind(...) -> Int` (same not-found semantics).
  - `stdlib/httplib/core.flv`: internal find helpers with `Int` not-found semantics.
- [~] Refinement target (in progress):
  - [x] Added additive Option-based APIs `strFindOpt` and `bytesFindOpt` while preserving existing `Int` APIs.
  - [x] Add migration note in release docs (prefer Option forms in new code).
  - [x] `httplib/core` now consumes shared `stringlib` / `bytelib` find helpers (unified implementation path).

## 3) Option/Result Ergonomics
- [ ] Ensure paired APIs are available and consistent:
  - `mapGet` + `mapGetOr`
  - `heapPeek` + `heapPeekOr`
  - `queuePeek` + `queuePeekOr`
- [ ] Add/confirm rule: when an operation can fail with context, prefer `Result`; for absence-only, prefer `Option`.

## 4) Module Prioritization (Execution Order)
1. `stdlib/stringlib/__init__.flv`
2. `stdlib/bytelib/__init__.flv`
3. `stdlib/httplib/core.flv`
4. `stdlib/regex/__init__.flv` (follow-up consistency pass) ✅

## 5) Required Test and Docs Updates Per Change
- [x] Add Python tests under `tests/test_stdlib_*`.
- [x] Add `.flv` behavior tests under `tests_flv/`.
- [x] Update docs pages under `docs/en/stdlib/` and `docs/zh/stdlib/`.
  - Updated module notes/examples for `regex`, `stringlib`, `bytelib`, and `httplib.core`.
- [x] Include deprecation/compat note in release notes for new additive aliases/APIs.
  - Added `docs/release_notes.md` and `docs/zh/release_notes.md`.
