# Bridge Usage Baseline

Date: 2026-02-19

## Bridge Surface
- Pure bridge primitives: `24`
- Effectful bridge primitives: `31`
- Total bridge symbols: `55`

## Stdlib Bridge Symbol References (Static)
- Total symbol references: `90`
- Distinct bridge symbols referenced: `55`
- Distinct stdlib modules referencing bridge symbols: `17`
- Top referenced bridge symbols:
- `strLen`: `11`
- `strCodeAt`: `7`
- `strSlice`: `7`
- `nowMillis`: `5`
- `pyAdapterCall`: `3`
- `strFromCode`: `3`
- `floatToStr`: `2`
- `monoMillis`: `2`
- Top stdlib modules by bridge references:
- `time/__init__`: `13`
- `fslib/__init__`: `10`
- `socket/api`: `8`
- `u32/__init__`: `7`
- `consoleIO/__init__`: `6`
- `hashlib/__init__`: `6`
- `bytelib/__init__`: `5`
- `file/lines`: `5`

## tests_flv Bridge Call Baseline
- Programs analyzed (expanded test cases): `83`
- Files analyzed: `25`
- Files failed to analyze: `0`
- Total audited bridge calls: `640`
- Bridge call kinds:
- `pure_call`: `564`
- `rpc`: `66`
- `call`: `10`
- Top audited calls:
- `pure_call:strLen`: `85`
- `pure_call:strCodeAt`: `71`
- `pure_call:strSlice`: `68`
- `pure_call:strFromCode`: `66`
- `pure_call:_pyBytesConcat`: `28`
- `pure_call:_pyBytesFromByte`: `28`
- `pure_call:_pyBytesGet`: `28`
- `pure_call:_pyBytesLen`: `28`
- `pure_call:_pyBytesSlice`: `28`
- `pure_call:_pyU32And`: `18`

## Notes
- stdlib_references are static token counts from stdlib/*.flv (excluding _bridge_python.flv).
- tests_flv_runtime_baseline uses compiler bridge audit counts after resolve/lower/typecheck.
