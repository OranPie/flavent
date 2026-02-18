# 发布说明（草案）

日期：2026-02-18

## 标准库 API 兼容性说明

- `stringlib` 新增 Option 风格查找：
  - `strFindOpt(h, needle, start) -> Option[Int]`
  - 原有 `strFind(...) -> Int` 继续保留（未找到返回 `-1`）。
- `bytelib` 新增：
  - `bytesFindOpt(h, needle, start) -> Option[Int]`
  - 原有 `bytesFind(...) -> Int` 继续保留（未找到返回 `-1`）。
- `httplib.core` 也新增 `strFindOpt` / `bytesFindOpt` 便于解析流程。
- `stringlib` 新增别名：
  - `strStartsWith`（等价 `startsWith`）
  - `strEndsWith`（等价 `endsWith`）

迁移建议：
- 新代码优先使用 Option 风格接口（`strFindOpt` / `bytesFindOpt`）。
- 旧代码继续使用 `strFind` / `bytesFind` 无需修改。

## 语言字面量行为说明

- 字符串字面量现支持常见 ASCII 转义：
  - `\"`, `\\`, `\n`, `\r`, `\t`, `\0`, `\a`, `\b`, `\f`, `\v`
- 字符串与字节字面量均支持 `\xNN` 十六进制转义。
- 字节字面量（`b"..."`）现在会保留解码后的真实字节值（如 `\x80`）。

兼容性说明：
- 若原程序依赖 `\n` 作为两个字符文本，请改写为 `\\n`。
- 未识别转义仍按原样保留以兼容现有场景（例如正则文本中的 `\d`）。
