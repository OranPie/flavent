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
