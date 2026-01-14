# `stringlib`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use stringlib
```

## 函数
```flavent
fn strFind(h: Str, needle: Str, start: Int) -> Int = do:
fn strContains(h: Str, needle: Str) -> Bool = strFind(h, needle, 0) >= 0
fn startsWith(h: Str, prefix: Str) -> Bool = do:
fn endsWith(h: Str, suffix: Str) -> Bool = do:
fn trimLeftSpaces(s: Str) -> Str = do:
fn trimRightSpaces(s: Str) -> Str = do:
fn trimSpaces(s: Str) -> Str = trimRightSpaces(trimLeftSpaces(s))
fn split(s: Str, sep: Str) -> List[Str] = do:
fn join(xs: List[Str], sep: Str) -> Str = _joinAcc(xs, sep, "")
```

