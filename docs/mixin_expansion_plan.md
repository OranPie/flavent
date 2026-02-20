# Mixin Expansion Plan (Phase Next)

Date: 2026-02-20

This plan extends current mixin capabilities beyond the existing sector hook baseline.

## Current Docs Status (Confirmed)

- [x] Core hook design doc exists: `docs/mixin_hooks.md`
- [x] Grammar reference includes mixin/hook syntax: `docs/grammar_ebnf.md`
- [x] Release notes track implemented hook work: `docs/release_notes.md`
- [x] Example coverage includes hook/mixin demos:
  - `examples/19_mixin_hook_chain.flv`
  - `examples/20_mixin_cancelable_override.flv`
- [~] EN/ZH user-facing dedicated mixin guide pages are still missing (`docs/en/...`, `docs/zh/...`)
- [~] No formal “mixin diagnostics catalog” document yet

## Goal

Deliver a stable, debuggable, policy-friendly mixin system with stronger composition controls, better diagnostics, and clear user docs.

## Phase A: Hook Target Coverage

- [x] Add `hook` support for type-target mixins (currently sector-only).
- [ ] Define hook support boundaries per callable kind (sector fn, type method, handler).
- [ ] Add compatibility rules for existing `around fn` behavior vs new hooks.
- [~] Tests:
  - [x] positive: type-target invoke/head/tail hooks
  - [x] negative: unsupported targets with precise diagnostics

## Phase B: Hook Context and Control

- [ ] Add structured hook context metadata (hook id, target, point, call depth).
- [ ] Add deterministic hook conflict policy options (`error`, `prefer`, `drop`).
- [ ] Add optional strict mode: unresolved `depends` or locator mismatch => hard error.
- [ ] Add “dry-run resolve” output for hook stack planning (for CI/debug).
- [ ] Tests:
  - [ ] conflict resolution behavior matrix
  - [ ] strict vs non-strict policy behavior

## Phase C: Diagnostics and Reporting

- [ ] Introduce stable mixin diagnostics/warning codes (e.g. `WMIX*`, `EMIX*`).
- [ ] Surface hook stack trace in `flavent check --report-json`.
- [ ] Add warning controls for mixin codes (suppress/escalate) aligned with check policy.
- [ ] Tests:
  - [ ] code presence + stage metadata
  - [ ] escalation/suppression flow

## Phase D: Docs and Examples

- [ ] Add EN guide: `docs/en/mixin_guide.md`
- [ ] Add ZH guide: `docs/zh/mixin_guide.md`
- [ ] Add diagnostics catalog page for mixin codes.
- [ ] Add 6+ focused examples:
  - [ ] type-target hook chain
  - [ ] conflict strategy demo
  - [ ] strict locator/dependency checks
  - [ ] reporting/CI policy example

## Exit Criteria

- [ ] Full suite green (`tests`, `tests_flv`, examples check).
- [ ] Mixin docs available in EN/ZH with migration notes.
- [ ] Structured reporting includes mixin diagnostics with stable codes.
- [ ] CI policy can enforce no-new-mixin-warnings.
