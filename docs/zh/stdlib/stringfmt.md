# `stringfmt`

## 概述
字符串格式化工具。

导入：
```flavent
use stringfmt
```

## API
- `format(tmpl: Str, args: List[Str]) -> Str`
- `formatWith(tmpl: Str, posArgs: List[Str], namedArgs: Map[Str, Str]) -> Str`
- `formatMap(tmpl: Str, args: Map[Str, Str]) -> Str`
