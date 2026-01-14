# `pyadapters`（自动生成）

## 概述
`pyadapters` 由 `flavent pkg install` 根据 `flm.json: pythonAdapters` 自动生成。

生成位置：
- `vendor/pyadapters/<adapter>.flv`
- `vendor/pyadapters/__init__.flv`

## Wrapper 约定
对于每个 adapter `name` 以及 allowlist 里的 method `<m>`，生成：

```flavent
sector <name>:
  fn <m>(payload: Bytes) -> Result[Bytes, Str] = rpc py.invoke("<name>", "<m>", payload)
```

使用示例：
```flavent
use pyadapters.demo
let r = rpc demo.echo(b"hi")
```
