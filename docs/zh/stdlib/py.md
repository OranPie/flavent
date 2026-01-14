# `py`（Python 适配器）

## 概述
`py` 是 Flavent 调用 Python 的**唯一**标准库入口。

- Flavent 代码不能直接 import Python。
- 只能通过 `_bridge_python.pyAdapterCall` 这一个受控闸门。
- 建议配合 `flm.json` + `flavent pkg install` 使用。

导入：
```flavent
use py
```

## API
- `invoke(adapter: Str, method: Str, payload: Bytes) -> Result[Bytes, Str]`

## v2 安全模型（子进程隔离）
- adapter 在独立子进程中运行。
- 运行时会调用 `__meta__` 读取 adapter 元信息，并进行强校验：
  - `capabilities` 必须是 adapter `CAPABILITIES` 的子集
  - `allow` 必须是 adapter `EXPORTS` 的子集

更多请参考仓库根目录的 `FLM_SPEC.md` 与 `docs/zh/FLM_SPEC.md`。
