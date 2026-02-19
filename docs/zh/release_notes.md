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

## 运行时性能说明

- 针对 FIFO 密集场景优化了事件循环内部实现：
  - 队列操作改为 `deque.popleft` 路径，
  - 事件分发增加按事件类型索引与堆调度。
- `match` 绑定恢复只处理实际绑定符号，不再复制整份环境字典。
- 未改变用户可见运行时语义（已通过全量测试验证）。

## Bridge 依赖基线工具

- 新增 `scripts/bridge_usage_snapshot.py`，用于采集 bridge 依赖指标。
- 新增基线产物：
  - `docs/bridge_usage_baseline.md`
  - `docs/bridge_usage_baseline.json`
- 当前快照覆盖：
  - `stdlib/_bridge_python.flv` 的 bridge 原语表面，
  - 标准库模块对 bridge 符号的静态引用，
  - 展开 `tests_flv` 用例后的 bridge 调用审计统计。

## 语法规划说明

- 新增 `docs/grammar_pain_points.md`，作为语法优化 Phase 1 的基线说明。
- 内容覆盖字面量、优先级可见性、模式匹配启发式与解析诊断等当前痛点。
- 新增 `docs/grammar_ebnf.md`，提供与当前解析器实现对齐的紧凑 EBNF 语法补充说明（Phase 2）。
- 改进了词法器字面量诊断：
  - `\x` 转义格式错误时，会明确提示“需要两个十六进制数字”，
  - 未终止字面量错误可区分 string 与 bytes。
- 解析器语法与诊断增强：
  - 表达式/事件/rpc/call/proceed 的参数列表支持尾随逗号，
  - 元组字面量支持尾随逗号（含单元素元组写法），
  - 常见分隔符缺失的报错增加了更有针对性的 expected-token 提示。
  - 声明级错误提示更具体：
    - type/const/let/need/pattern/function 中缺少 `=` 会给出更明确指导，
    - 在 sector 作用域误用赋值时会提示改用 `let`，
    - mixin 项目报错会按目标类型（sector/type）提示可用项。
  - 进一步的解析器提示优化：
    - 对 match arm 中 `->` 前后缺失 pattern/body 的报错更清晰，
    - 明确提示不支持单行 block 形式（`if/for/match` 需换行+缩进）。
