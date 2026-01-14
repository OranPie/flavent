# `py` (Python adapters)

## Overview
`py` is the **only** stdlib entry point for calling Python adapters.

- No direct Python imports from Flavent.
- Calls are routed through `_bridge_python.pyAdapterCall`.
- Intended to be used together with `flm.json` + `flavent pkg install`.

Import:
```flavent
use py
```

## API
- `invoke(adapter: Str, method: Str, payload: Bytes) -> Result[Bytes, Str]`

## Protocol (v2)
- The adapter runs in a subprocess.
- Parent process queries `__meta__` and enforces:
  - requested `capabilities` ⊆ adapter `CAPABILITIES`
  - requested `allow` ⊆ adapter `EXPORTS`

See also:
- `FLM_SPEC.md` at repo root.
