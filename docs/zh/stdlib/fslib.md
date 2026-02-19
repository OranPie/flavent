# `fslib`

## 概述
底层文件系统操作（直接封装 `_bridge_python`）。

建议：
- 若只需要常用读写，优先使用 `file` 模块。

## API 归属与迁移建议
- `fslib` 是贴近 bridge 的底层文件系统层。
- 对应用代码，重名能力优先使用 `file.*`：
  - `exists`、`listDir`、`remove`、`tempFile`、`tempDir`
- 仅在需要底层 bridge 原语时直接使用 `fslib`。

## 导入
```flavent
use fslib
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn readFileBytes(path: Str) -> Result[Bytes, Str] = rpc _bridge_python.fsReadFileBytes(path)
fn readFileStr(path: Str) -> Result[Str, Str] = rpc _bridge_python.fsReadFileStr(path)
fn writeFileBytes(path: Str, data: Bytes) -> Result[Unit, Str] = rpc _bridge_python.fsWriteFileBytes(path, data)
fn writeFileStr(path: Str, data: Str) -> Result[Unit, Str] = rpc _bridge_python.fsWriteFileStr(path, data)
fn listDir(path: Str) -> Result[List[Str], Str] = rpc _bridge_python.fsListDir(path)
fn exists(path: Str) -> Result[Bool, Str] = rpc _bridge_python.fsExists(path)
fn mkdirs(path: Str) -> Result[Unit, Str] = rpc _bridge_python.fsMkdirs(path)
fn remove(path: Str) -> Result[Unit, Str] = rpc _bridge_python.fsRemove(path)
fn tempFile(prefix: Str, suffix: Str) -> Result[Str, Str] = rpc _bridge_python.fsTempFile(prefix, suffix)
fn tempDir(prefix: Str) -> Result[Str, Str] = rpc _bridge_python.fsTempDir(prefix)
```
<!-- AUTO-GEN:END FUNCTIONS -->
