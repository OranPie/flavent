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
- [x] Publish a compact EBNF-style grammar supplement in docs.
  - Added: `docs/grammar_ebnf.md`
- [~] Tighten literal grammar and diagnostics (invalid escapes, malformed bytes/hex, recoverable parser errors).
  - [x] Improved literal diagnostics in lexer:
    - invalid `\x` now reports explicit expectation of two hex digits
    - unterminated literals now distinguish `string` vs `bytes`
  - [~] Parser-side recovery diagnostics follow-up:
    - [x] `expect(...)` paths now include token-specific hints (`:`, `)`, `]`, `->`)
    - [ ] expand recoverable multi-error parsing in future pass
- [~] Add parser/lexer regression tests for ambiguous and edge-case constructs.
  - [x] Added parser regression coverage for precedence and trailing-comma forms.
  - [x] Added parser/runtime coverage for sector mixin hook forms (`head`/`tail`/`invoke`) and resolver ordering.
  - [ ] Expand to additional ambiguity classes (match arms, mixin forms, nested blocks).
- [~] Improve user-facing error messages with expected-token hints.
  - [x] Added expected-token hints in core parser `expect` paths.
  - [~] Added context-sensitive declaration-level hints:
    - [x] function/type/const/let/need/pattern declaration `'='` guidance
    - [x] sector-item scope hint (`let` vs assignment at sector scope)
    - [x] mixin target-specific expected-item guidance
    - [x] match-arm structure hints (missing pattern/body around `->`)
    - [x] explicit block-form hint for single-line `if/for/match` style misuse
    - [ ] continue expanding hints for additional malformed declaration patterns
  - [x] Added hook-target locator diagnostics (`at` anchor/line mismatch).

- [x] Prototype hook-oriented mixin extension and metadata helper package:
  - sector mixin `hook head|tail|invoke` syntax with `with(...)` options
  - priority/dependency call-stack resolver for hooks
  - `flvrepr` package for string metadata encoding/decoding
  - stricter hook semantic validation:
    - reject unknown `with(...)` option keys
    - enforce `cancelable=true` return type as `Option[targetRet]`
    - enforce tail `returnDep` value set and previous-return param typing
  - docs coverage:
    - add `flvrepr` stdlib docs pages (`docs/en/stdlib/flvrepr.md`, `docs/zh/stdlib/flvrepr.md`)
    - include `flvrepr` in stdlib index pages

## Phase 3: Compiler Structure Improvements
- [~] Split parser/lexer helper logic into clearer internal units (without public API breakage).
  - [x] Extracted hook `with(...)` option parsing into `_parse_hook_with_options` helper.
  - [ ] Continue splitting large parser sections and shared parse utilities.
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
