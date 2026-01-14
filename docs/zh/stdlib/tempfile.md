# `tempfile`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use tempfile
```

## 函数
```flavent
fn mkstemp(prefix: Str, suffix: Str) -> Result[Str, Str] = rpc fslib.tempFile(prefix, suffix)
fn mkdtemp(prefix: Str) -> Result[Str, Str] = rpc fslib.tempDir(prefix)
```

