# `uuid`

## Overview
UUID v4 generation and parsing.

Import:
```flavent
use uuid
```

## API
- `uuid4() -> Bytes`
- `toString(u: Bytes) -> Str`
- `parse(s: Str) -> Result[Bytes, Str]`
