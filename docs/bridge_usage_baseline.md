# Bridge Usage Baseline

Date: 2026-02-19

## Bridge Surface
- Pure bridge primitives: `24`
- Effectful bridge primitives: `31`
- Total bridge symbols: `55`

## Stdlib Bridge Symbol References (Static)
- Total symbol references: `66`
- Distinct bridge symbols referenced: `55`
- Distinct stdlib modules referencing bridge symbols: `12`
- Top referenced bridge symbols:
- `nowMillis`: `5`
- `pyAdapterCall`: `3`
- `floatToStr`: `2`
- `monoMillis`: `2`
- `monoNanos`: `2`
- `nowNanos`: `2`
- `sleep`: `2`
- `_pyBytesConcat`: `1`
- Top stdlib modules by bridge references:
- `time/__init__`: `13`
- `fslib/__init__`: `10`
- `socket/api`: `8`
- `u32/__init__`: `7`
- `consoleIO/__init__`: `6`
- `hashlib/__init__`: `6`
- `bytelib/__init__`: `5`
- `stringlib/__init__`: `4`

## tests_flv Bridge Call Baseline
- Programs analyzed (expanded test cases): `83`
- Files analyzed: `25`
- Files failed to analyze: `0`
- Total audited bridge calls: `562`
- Bridge call kinds:
- `pure_call`: `486`
- `rpc`: `66`
- `call`: `10`
- Top audited calls:
- `pure_call:strCodeAt`: `53`
- `pure_call:strFromCode`: `53`
- `pure_call:strLen`: `53`
- `pure_call:strSlice`: `53`
- `pure_call:_pyBytesConcat`: `28`
- `pure_call:_pyBytesFromByte`: `28`
- `pure_call:_pyBytesGet`: `28`
- `pure_call:_pyBytesLen`: `28`
- `pure_call:_pyBytesSlice`: `28`
- `pure_call:_pyU32And`: `18`

## Notes
- stdlib_references are static token counts from stdlib/*.flv (excluding _bridge_python.flv).
- tests_flv_runtime_baseline uses compiler bridge audit counts after resolve/lower/typecheck.
