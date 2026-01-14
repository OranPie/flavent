# `base64`

## 概述
Base64 编解码。

导入：
```flavent
use base64
```

## API
- `encode(b: Bytes) -> Str`
- `decode(s: Str) -> Result[Bytes, Str]`
- `urlsafeEncode(b: Bytes) -> Str`
- `urlsafeDecode(s: Str) -> Result[Bytes, Str]`
