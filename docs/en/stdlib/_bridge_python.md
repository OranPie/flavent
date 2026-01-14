# `_bridge_python` (internal)

## Overview
`_bridge_python` is an internal capability boundary.

- User programs must **not** `use _bridge_python` directly.
- Stdlib modules wrap bridge functions and expose safe APIs.

Notable functions:
- time, filesystem, console, sockets
- `pyAdapterCall(adapter, method, payload) -> Result[Bytes, Str]` (python adapter gate)
