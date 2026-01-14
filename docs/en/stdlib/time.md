# `time`

## Overview
System time and sleep.

Import:
```flavent
use time
```

## API
- `nowMillis() -> Result[Int, Str]`
- `nowNanos() -> Result[Int, Str]`
- `monoMillis() -> Result[Int, Str]`
- `monoNanos() -> Result[Int, Str]`
- `sleepMillis(ms: Int) -> Unit`
