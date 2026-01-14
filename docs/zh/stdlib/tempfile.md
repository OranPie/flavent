# `tempfile`

## 概述
临时文件/目录。

导入：
```flavent
use tempfile
```

## API
- `mkstemp(prefix: Str, suffix: Str) -> Result[Str, Str]`
- `mkdtemp(prefix: Str) -> Result[Str, Str]`
