# `file`

## 概述
高层文件操作（建立在 `fslib` 之上）。

约定：
- `read*` 返回 `Result[...]`（避免异常）。
- `write*`/`append*` 返回 `Result[Unit, Str]`。

性能提示：
- `appendBytes/appendText` 当前实现是 **read+concat+write**，对大文件不适合。

## API 归属与迁移建议
- `file` 是面向应用代码的规范文件系统命名空间。
- 与 `fslib` 重名的 API（`exists`、`listDir`、`remove`、`tempFile`、`tempDir`）是有意保留的兼容层。
- 新代码优先使用 `file.*`。

## 导入
```flavent
use file
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn readBytes(path: Str) -> Result[Bytes, Str] = rpc fslib.readFileBytes(path)
fn readText(path: Str) -> Result[Str, Str] = rpc fslib.readFileStr(path)
fn writeBytes(path: Str, data: Bytes) -> Result[Unit, Str] = do:
fn writeText(path: Str, data: Str) -> Result[Unit, Str] = do:
fn appendBytes(path: Str, data: Bytes) -> Result[Unit, Str] = do:
fn appendText(path: Str, data: Str) -> Result[Unit, Str] = do:
fn ensureDir(path: Str) -> Result[Unit, Str] = do:
fn remove(path: Str) -> Result[Unit, Str] = do:
fn exists(path: Str) -> Result[Bool, Str] = rpc fslib.exists(path)
fn listDir(path: Str) -> Result[List[Str], Str] = rpc fslib.listDir(path)
fn tempFile(prefix: Str, suffix: Str) -> Result[Str, Str] = rpc fslib.tempFile(prefix, suffix)
fn tempDir(prefix: Str) -> Result[Str, Str] = rpc fslib.tempDir(prefix)
fn readLines(path: Str) -> Result[List[Str], Str] = do:
fn writeLines(path: Str, xs: List[Str]) -> Result[Unit, Str] = writeText(path, joinLines(xs))
fn appendLine(path: Str, line: Str) -> Result[Unit, Str] = appendText(path, "\n" + line)
fn appendLines(path: Str, xs: List[Str]) -> Result[Unit, Str] = match xs:
```
<!-- AUTO-GEN:END FUNCTIONS -->
