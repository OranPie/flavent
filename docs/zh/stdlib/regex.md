# `regex`

## 概述
纯 Flavent 正则引擎。

导入：
```flavent
use regex
```

## API
- `compile(pattern: Str) -> Result[Regex, Str]`
- `isMatch(re: Regex, s: Str) -> Bool`
- `findFirst(re: Regex, s: Str) -> Option[Str]`
