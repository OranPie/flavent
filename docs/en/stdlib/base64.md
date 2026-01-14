# `base64`

## Overview
Base64 encoding/decoding.

Import:
```flavent
use base64
```

## API
- `encode(b: Bytes) -> Str`
- `decode(s: Str) -> Result[Bytes, Str]`
- `urlsafeEncode(b: Bytes) -> Str`
- `urlsafeDecode(s: Str) -> Result[Bytes, Str]`
