# `_bridge_python`（内部）

## 概述
`_bridge_python` 是内部能力边界：
- 用户程序 **禁止** 直接 `use _bridge_python`。
- 标准库通过 wrapper 暴露安全 API。

包含：
- 时间、文件系统、控制台、socket
- `pyAdapterCall(adapter, method, payload) -> Result[Bytes, Str]`（Python adapter 唯一闸门）
