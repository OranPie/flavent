# `file.lines`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use file.lines
```

## 函数
```flavent
fn splitLines(s: Str) -> List[Str] = _linesSplitAcc(s, 0, 0, Nil)
fn joinLines(xs: List[Str]) -> Str = _joinLines(xs)
```

