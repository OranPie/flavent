# `time`

## 概述
系统时间与 sleep。

导入：
```flavent
use time
```

## API
- `nowMillis() -> Result[Int, Str]`
- `nowNanos() -> Result[Int, Str]`
- `monoMillis() -> Result[Int, Str]`
- `monoNanos() -> Result[Int, Str]`
- `sleepMillis(ms: Int) -> Unit`
