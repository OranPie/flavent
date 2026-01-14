# `fslib`

## Overview
Filesystem operations via the host bridge.

Import:
```flavent
use fslib
```

## API
- `readFileBytes(path: Str) -> Result[Bytes, Str]`
- `readFileStr(path: Str) -> Result[Str, Str]`
- `writeFileBytes(path: Str, data: Bytes) -> Result[Unit, Str]`
- `writeFileStr(path: Str, data: Str) -> Result[Unit, Str]`
- `listDir(path: Str) -> Result[List[Str], Str]`
- `exists(path: Str) -> Result[Bool, Str]`
- `mkdirs(path: Str) -> Result[Unit, Str]`
- `remove(path: Str) -> Result[Unit, Str]`
- `tempFile(prefix: Str, suffix: Str) -> Result[Str, Str]`
- `tempDir(prefix: Str) -> Result[Str, Str]`
