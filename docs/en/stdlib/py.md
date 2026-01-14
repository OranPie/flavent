# `py`

## Overview
Single entry point for Python adapters (v2: subprocess isolation).

Rules:
- Flavent code must not import Python directly.
- Calls go through `py.invoke(adapter, method, payload)`.
- Prefer using generated wrappers in `pyadapters`.

See also:
- `docs/en/stdlib/pyadapters.md`

## Import
```flavent
use py
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn invoke(adapter: Str, method: Str, payload: Bytes) -> Result[Bytes, Str] = rpc _bridge_python.pyAdapterCall(adapter, method, payload)
```
<!-- AUTO-GEN:END FUNCTIONS -->
