# `uuid`

## 概述
UUID v4 生成与解析。

导入：
```flavent
use uuid
```

## API
- `uuid4() -> Bytes`
- `toString(u: Bytes) -> Str`
- `parse(s: Str) -> Result[Bytes, Str]`
