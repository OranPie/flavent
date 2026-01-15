# `json`

## Overview
JSON encoding/decoding.

Notes:
- `loads` returns `Result[JsonValue, Str]`.
- Numbers support integers (`JInt`) and floats (`JFloat`), including scientific notation.
- String escapes include `\\uXXXX` (basic Unicode).
- Whitespace is skipped (space / tab / newline / carriage return).

## Example

```flavent
use json
use std.result

let r = loads("{\"a\": 1}")
```

## Import
```flavent
use json
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type JsonValue = JNull | JBool(Bool) | JInt(Int) | JFloat(Float) | JStr(Str) | JArr(List[JsonValue]) | JObj(Map[Str, JsonValue])
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn jNull() -> JsonValue = JNull
fn dumps(j: JsonValue) -> Str = match j:
fn loads(s: Str) -> Result[JsonValue, Str] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
