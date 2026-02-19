# `fslib`

## Overview
Low-level filesystem operations (thin wrappers over `_bridge_python`).

If you only need common read/write helpers, prefer the higher-level `file` module.

## API Ownership & Migration
- `fslib` is the canonical bridge-near filesystem layer.
- For app code, prefer `file.*` for overlapping names:
  - `exists`, `listDir`, `remove`, `tempFile`, `tempDir`
- Keep using `fslib` when you need low-level bridge-oriented primitives directly.

## Import
```flavent
use fslib
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
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
