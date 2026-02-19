# `stringlib`

## 概述
字符串工具，强调可预测行为与简单组合。

说明：
- `strFind` 未找到时返回 `-1`。
- `strFindOpt` 返回 `Some(index)` / `None`，新代码建议优先使用。
- `startsWith`/`endsWith` 与 `strStartsWith`/`strEndsWith` 等价（兼容别名）。
- `strLength`/`strCode`/`strSliceRange`/`strFromCodePoint` 提供低层桥接能力，便于其他 stdlib 模块复用。

## 导入
```flavent
use stringlib
```

## 示例
```flavent
let i0 = strFind("abcabc", "bc", 0)     // 1
let i1 = strFindOpt("abc", "z", 0)      // None
let ok = strStartsWith("hello", "he")   // true
let out = trimSpaces("  hi  ")          // "hi"
```

## 函数
```flavent
fn strFind(h: Str, needle: Str, start: Int) -> Int = do:
fn strFindOpt(h: Str, needle: Str, start: Int) -> Option[Int] = do:
fn strContains(h: Str, needle: Str) -> Bool = strFind(h, needle, 0) >= 0
fn strLength(s: Str) -> Int = strLen(s)
fn strCode(s: Str, i: Int) -> Int = strCodeAt(s, i)
fn strSliceRange(s: Str, a: Int, b: Int) -> Str = strSlice(s, a, b)
fn strFromCodePoint(code: Int) -> Str = strFromCode(code)
fn startsWith(h: Str, prefix: Str) -> Bool = do:
fn endsWith(h: Str, suffix: Str) -> Bool = do:
fn strStartsWith(h: Str, prefix: Str) -> Bool = startsWith(h, prefix)
fn strEndsWith(h: Str, suffix: Str) -> Bool = endsWith(h, suffix)
fn trimLeftSpaces(s: Str) -> Str = do:
fn trimRightSpaces(s: Str) -> Str = do:
fn trimSpaces(s: Str) -> Str = trimRightSpaces(trimLeftSpaces(s))
fn split(s: Str, sep: Str) -> List[Str] = do:
fn join(xs: List[Str], sep: Str) -> Str = _joinAcc(xs, sep, "")
```
