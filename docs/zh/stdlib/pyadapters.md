# `pyadapters`（自动生成）

## 概述
`pyadapters` 由 `flavent pkg install` 根据 `flm.json: pythonAdapters` 自动生成。

生成位置：
- `vendor/pyadapters/<adapter>.flv`
- `vendor/pyadapters/__init__.flv`

## Wrapper 约定
对于每个 adapter `name` 以及 wrapper `<m>`，生成：

```flavent
sector <name>:
  fn <m>(payload: Bytes) -> Result[Bytes, Str] = rpc py.invoke("<name>", "<m>", payload)
```

使用示例：
```flavent
use pyadapters.demo
let r = rpc demo.echo(b"hi")
```

## Wrapper 配置
可以通过 `flm.json` 定义 wrapper 签名：

```json
{
  "pythonAdapters": [
    {
      "name": "demo",
      "allow": ["echo", "echoText", "sum"],
      "wrappers": [
        "echo",
        { "name": "echoText", "codec": "text", "args": ["Str"], "ret": "Str" },
        { "name": "sum", "codec": "json", "args": ["Int", "Int"], "ret": "Int" }
      ]
    }
  ]
}
```

支持的 `codec`：
- `bytes`（默认）：`(Bytes) -> Bytes`
- `text`：`(Str) -> Str`（ASCII 编码）
- `json`：参数打包为 JSON 数组，返回为 JSON value

`json` codec 支持 `Int`、`Float`、`Bool`、`Str`、`JsonValue`、`Unit`。

Wrapper 条目可以是字符串（bytes codec）或对象（`name`/`codec`/`args`/`ret`）。
如果省略 `wrappers`，会从 `allow` 推导并默认使用 bytes codec。
