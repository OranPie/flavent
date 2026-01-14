# `json`

## Overview
JSON encoding/decoding.

Notes:
- `loads` returns `Option[Json]` (parse failure is `None`).
- Numbers are currently **integers only** (`JInt`).
- Whitespace is skipped (space / tab / newline / carriage return).

## Example

```flavent
use json
use std.option

let v = loads("{\"a\": 1}")
```

## Import
```flavent
use json
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Json = JNull | JBool(Bool) | JInt(Int) | JStr(Str) | JArr(List[Json]) | JObj(Map[Str, Json])
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn jNull() -> Json = JNull
fn dumps(j: Json) -> Str = match j:
fn loads(s: Str) -> Option[Json] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
