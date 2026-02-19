# Release Notes (Working Draft)

Date: 2026-02-18

## Stdlib API Compatibility Notes

- `stringlib` now exposes Option-first find APIs:
  - `strFindOpt(h, needle, start) -> Option[Int]`
  - Existing `strFind(...) -> Int` remains supported (`-1` when not found).
- `bytelib` now exposes:
  - `bytesFindOpt(h, needle, start) -> Option[Int]`
  - Existing `bytesFind(...) -> Int` remains supported (`-1` when not found).
- `httplib.core` now also exposes `strFindOpt` and `bytesFindOpt` for parsing flows.
- `stringlib` alias additions:
  - `strStartsWith` alias of `startsWith`
  - `strEndsWith` alias of `endsWith`

Migration guidance:
- New code should prefer Option-based forms (`strFindOpt` / `bytesFindOpt`) over sentinel `-1` checks.
- Existing code using `strFind` / `bytesFind` does not need changes.

## Language Literal Behavior Notes

- String literals now decode common ASCII escapes:
  - `\"`, `\\`, `\n`, `\r`, `\t`, `\0`, `\a`, `\b`, `\f`, `\v`
- `\xNN` hex escapes are now supported in both strings and bytes literals.
- Bytes literals (`b"..."`) now preserve decoded byte values (including `\x80` etc.) as actual bytes.

Compatibility note:
- Programs that intentionally relied on literal text `\n` being two characters should now use `\\n` for that exact text.
- Unknown escapes remain preserved as-is for compatibility (for example regex-like `\d` text literals).

## Runtime Performance Notes

- Event-loop internals were optimized for FIFO-heavy workloads:
  - queue operations now use deque-based `popleft` paths,
  - event dispatch uses event-type indexing and heap scheduling.
- Match arm binding now restores only touched symbols instead of copying full environments.
- No user-visible runtime semantics were changed (validated by full test suite).

## Bridge Usage Baseline Tooling

- Added `scripts/bridge_usage_snapshot.py` to capture bridge-dependency metrics.
- Added baseline artifacts:
  - `docs/bridge_usage_baseline.md`
  - `docs/bridge_usage_baseline.json`
- This snapshot tracks:
  - bridge primitive surface in `stdlib/_bridge_python.flv`,
  - static bridge symbol references across stdlib modules,
  - audited bridge call usage across expanded `tests_flv` cases.

## Grammar Planning Notes

- Added `docs/grammar_pain_points.md` as a Phase 1 baseline for grammar refinement work.
- Captures current pain points for literals, precedence visibility, pattern parsing heuristics, and parser diagnostics.
- Added `docs/grammar_ebnf.md` as a compact Phase 2 EBNF-style grammar supplement aligned with current parser behavior.
- Improved lexer literal diagnostics:
  - malformed `\x` escapes now report explicit `two hex digits after \x` guidance,
  - unterminated literal errors now distinguish string vs bytes literals.
- Parser grammar and diagnostics refinements:
  - expression/event/rpc/call/proceed argument lists now accept trailing commas,
  - tuple literals now accept trailing commas (including single-element tuple form),
  - expected-token parse errors now include targeted hints for common delimiters.
  - declaration-level parse hints improved for common mistakes:
    - missing `=` in type/const/let/need/pattern/function declarations,
    - sector-scope assignment misuse now suggests `let`,
    - mixin item errors now mention valid items per mixin target (sector vs type).
  - additional parser guidance:
    - clearer match-arm errors for missing pattern/body around `->`,
    - explicit reminder that single-line block forms are unsupported (`if/for/match` require newline+indent blocks).
  - mixin hook grammar added for sector mixins:
    - `hook head|tail|invoke fn ... with(...) = ...`
    - option keys include `id`, `priority`, `depends`, `at`, `cancelable`, `returnDep`, `const`.
  - resolver now supports hook call-stack ordering with priority/dependency resolution and locator checks (`at`).
  - added `flvrepr` stdlib package for string-based metadata encoding/decoding (`encodeFunctionTarget`, `metaGet`, `metaSet`).
