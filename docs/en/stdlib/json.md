# `json`

## Overview
JSON encoding/decoding.

Import:
```flavent
use json
```

## API
- `loads(s: Str) -> Result[JsonValue, Str]`
- `dumps(v: JsonValue) -> Str`
- `jNull() -> JsonValue`
