# Release Notes (Working Draft)

Date: 2026-02-19

## Discard Binding Configuration

- Added auto-discard bindings for variable declarations.
- Default discard name is `_`:
  - repeated bindings like `let _ = ...` no longer trigger duplicate-name errors.
  - discard names are not resolvable as normal variables.
- Discard names are configurable via nearest `flvdiscard` file:
  - searched upward from the source file directory.
  - supports whitespace/comma-separated identifiers and `#` comments.

## Stdlib API Compatibility Notes

- `stringlib` now exposes Option-first find APIs:
  - `strFindOpt(h, needle, start) -> Option[Int]`
  - Existing `strFind(...) -> Int` remains supported (`-1` when not found).
- `bytelib` now exposes:
  - `bytesFindOpt(h, needle, start) -> Option[Int]`
  - Existing `bytesFind(...) -> Int` remains supported (`-1` when not found).
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
- Refreshed baseline after bridge-wrapper consolidation (`2026-02-19`):
  - total bridge symbols: `55` (24 pure + 31 effectful),
  - stdlib bridge references: `66` across `12` modules (down from `226` across `26`),
  - audited `tests_flv` bridge calls: `562` (pure_call `486`, rpc `66`, call `10`; down from `1711`).
- Added reusable low-level string wrappers in `stringlib` and migrated core modules (`url`, `path`, `datetime`, `csv`, `cliargs`, `regex`, `httplib.core`, `struct`, `json`, `hashlib.sha256`, `py`, `process`, `file.lines`, `glob`, `uuid`, `base64.core`, `asciilib`, `stringfmt`) to reduce direct bridge coupling.
- `stdlib/flvrepr` now avoids direct `_bridge_python` imports by using `stringlib`/`collections.list` helpers.
- `stdlib/httplib.core` now delegates shared helpers to connected stdlib modules (`stringlib`, `bytelib`, `asciilib`) for find/trim/ascii conversions.
- Added duplicate-definition detector/report for stdlib cross-module symbols:
  - `scripts/stdlib_duplicate_defs.py`
  - `docs/stdlib_duplicate_defs.md`
- Added duplicate policy allowlist + ownership table:
  - `docs/stdlib_duplicate_allowlist.json`
  - `docs/stdlib_api_ownership.md`
- Added direct bridge-import boundary policy tooling:
  - `scripts/stdlib_bridge_boundary.py`
  - `docs/stdlib_bridge_boundary_allowlist.json`
  - CI now enforces both unapproved bridge-import modules and stale allowlist entries.
- Improved check reporting and warning controls:
  - new structured report output: `flavent check ... --report-json <path>`
  - warning controls: `--warn-as-error`, `--warn-code-as-error`, `--suppress-warning`, `--max-warnings`
  - warning issues now include stable code metadata (`WBR001`) for policy and CI automation.
- Unified reporting schema (`schema_version: 1.0`) for stdlib policy tooling JSON outputs:
  - `scripts/bridge_usage_snapshot.py`
  - `scripts/stdlib_duplicate_defs.py`
  - `scripts/stdlib_bridge_boundary.py`
  - raw payloads now live under `artifacts.<tool_name>` for stable machine consumption.
- Added warning code catalog docs:
  - `docs/warning_catalog.md`
  - `docs/zh/warning_catalog.md`
- Duplicate CI policy now fails only on **unapproved** public duplicates:
  - internal modules (`_bridge_python`, `testns.*`) are excluded by default,
  - approved `file`/`fslib` overlap is tracked explicitly by allowlist entries.

## Stdlib Expansion (Phase 2 Kickoff)

- Added new `env` stdlib module with `Result`-based env-style operations:
  - `envGet` / `envGetOr` / `envSet` / `envUnset`
  - `envHas` / `envList` / `envClear`
  - deterministic explicit `Env` state value (`envEmpty` bootstrap)
- Added new `process` stdlib module with structured process simulation API:
  - spec builders: `processSpec`, `processWith*`
  - lifecycle: `processSpawn`, `processStart`, `processWait`, `processRun`
  - structured errors via `ProcessError { code, message }`
- Added new `cliargs` stdlib module for deterministic argv parsing:
  - `cliParse`, `cliHasFlag`, `cliGetOption`, `cliPositionals`
  - supports long options, short flag bundles, and `--` terminator
- Added new `log` stdlib module for leveled console logging:
  - `logLevel*` helpers and configurable `Logger` (`logDefault`, `logNamed`)
  - pure helpers: `logShouldEmit`, `logRecord`, `logFormat`, `logPrepare`
  - effectful emitters in `sector log`: `logInfo`, `logWarn`, `logError`, etc.
- Added new `collections.deque` stdlib module (plus `deque` compatibility wrapper):
  - `dequePushFront` / `dequePushBack`
  - `dequePopFront` / `dequePopBack`
  - `dequePeekFront` / `dequePeekBack` and list conversion helpers
- Added new `datetime` stdlib module with pure-Flavent helpers:
  - `parseDate` / `parseTime` / `parseDateTime`
  - `formatDate` / `formatTime` / `formatDateTime`
  - `Date` / `Time` / `DateTime` validity helpers
- Added new `path` stdlib module with pure-Flavent helpers:
  - `pathNormalize` / `pathJoin` / `pathJoinAll`
  - `pathBase` / `pathDir` / `pathExt` / `pathStem`
- Added new `csv` stdlib module with pure-Flavent helpers:
  - `csvParseLine` / `csvParse`
  - `csvStringifyLine` / `csvStringify`
  - `CsvOptions` for delimiter/quote configuration
- Added new `url` stdlib module with pure-Flavent helpers:
  - `encodeComponent` / `decodeComponent`
  - `queryEncode` / `queryDecode`
  - `queryParse` / `queryBuild`
- Added EN/ZH docs pages and index links:
  - `docs/en/stdlib/env.md`
  - `docs/zh/stdlib/env.md`
  - `docs/en/stdlib/process.md`
  - `docs/zh/stdlib/process.md`
  - `docs/en/stdlib/cliargs.md`
  - `docs/zh/stdlib/cliargs.md`
  - `docs/en/stdlib/log.md`
  - `docs/zh/stdlib/log.md`
  - `docs/en/stdlib/collections.deque.md`
  - `docs/zh/stdlib/collections.deque.md`
  - `docs/en/stdlib/deque.md`
  - `docs/zh/stdlib/deque.md`
  - `docs/en/stdlib/datetime.md`
  - `docs/zh/stdlib/datetime.md`
  - `docs/en/stdlib/path.md`
  - `docs/zh/stdlib/path.md`
  - `docs/en/stdlib/csv.md`
  - `docs/zh/stdlib/csv.md`
  - `docs/en/stdlib/url.md`
  - `docs/zh/stdlib/url.md`

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
  - hook semantic checks were tightened:
    - unknown `with(...)` option keys are now rejected,
    - `head + cancelable=true` now requires return type `Option[targetReturnType]`,
    - `tail + returnDep` now validates allowed values and previous-return parameter typing.
  - added `flvrepr` stdlib package for string-based metadata encoding/decoding (`encodeFunctionTarget`, `metaGet`, `metaSet`).
