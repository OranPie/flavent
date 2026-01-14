# `stringlib`

## 概述
ASCII 字符串基础工具库。

导入：
```flavent
use stringlib
```

## API
- `strFind(haystack, needle, start) -> Int`
- `strContains(haystack, needle) -> Bool`
- `startsWith(haystack, prefix) -> Bool`
- `endsWith(haystack, suffix) -> Bool`
- `trimLeftSpaces(s) -> Str`
- `trimRightSpaces(s) -> Str`
- `trimSpaces(s) -> Str`
- `split(s, sep) -> List[Str]`
- `join(xs, sep) -> Str`

说明：
- `trim*Spaces` 当前只处理 ASCII 空格（code 32）。
