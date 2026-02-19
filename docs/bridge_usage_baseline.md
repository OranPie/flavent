# Bridge Usage Baseline

Date: 2026-02-19

## Bridge Surface
- Pure bridge primitives: `24`
- Effectful bridge primitives: `31`
- Total bridge symbols: `55`

## Stdlib Bridge Symbol References (Static)
- Total symbol references: `226`
- Distinct bridge symbols referenced: `55`
- Distinct stdlib modules referencing bridge symbols: `26`
- Top referenced bridge symbols:
- `strLen`: `69`
- `strSlice`: `45`
- `strCodeAt`: `32`
- `strFromCode`: `18`
- `nowMillis`: `5`
- `pyAdapterCall`: `3`
- `floatToStr`: `2`
- `monoMillis`: `2`
- Top stdlib modules by bridge references:
- `httplib/core`: `23`
- `url/__init__`: `23`
- `stringlib/__init__`: `19`
- `datetime/__init__`: `15`
- `path/__init__`: `14`
- `time/__init__`: `13`
- `struct/__init__`: `12`
- `fslib/__init__`: `10`

## tests_flv Bridge Call Baseline
- Programs analyzed (expanded test cases): `82`
- Files analyzed: `25`
- Files failed to analyze: `0`
- Total audited bridge calls: `1711`
- Bridge call kinds:
- `pure_call`: `1635`
- `rpc`: `66`
- `call`: `10`
- Top audited calls:
- `pure_call:strLen`: `649`
- `pure_call:strCodeAt`: `309`
- `pure_call:strSlice`: `307`
- `pure_call:strFromCode`: `96`
- `pure_call:_pyBytesConcat`: `28`
- `pure_call:_pyBytesFromByte`: `28`
- `pure_call:_pyBytesGet`: `28`
- `pure_call:_pyBytesLen`: `28`
- `pure_call:_pyBytesSlice`: `28`
- `pure_call:_pyU32And`: `18`

## Notes
- stdlib_references are static token counts from stdlib/*.flv (excluding _bridge_python.flv).
- tests_flv_runtime_baseline uses compiler bridge audit counts after resolve/lower/typecheck.
