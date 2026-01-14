# `json`

## 概述
JSON 编解码。

导入：
```flavent
use json
```

## API
- `loads(s: Str) -> Result[JsonValue, Str]`
- `dumps(v: JsonValue) -> Str`
- `jNull() -> JsonValue`
