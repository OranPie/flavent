# `path`

## 概述
纯 Flavent 实现的路径处理工具。

能力包括：
- 统一分隔符并规范化 `.` / `..` 路径段。
- 路径拼接。
- 提取文件名、目录名、扩展名和 stem。

## 导入
```flavent
use path
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn pathIsAbs(p: Str) -> Bool = startsWith(_canonSep(p), "/")
fn pathNormalize(p: Str) -> Str = do:
fn pathJoin(a: Str, b: Str) -> Str = do:
fn pathJoinAll(parts: List[Str]) -> Str = _pathJoinAllAcc(parts, "")
fn pathBase(p: Str) -> Str = do:
fn pathDir(p: Str) -> Str = do:
fn pathExt(p: Str) -> Str = do:
fn pathStem(p: Str) -> Str = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
