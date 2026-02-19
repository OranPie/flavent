# 发布说明（草案）

日期：2026-02-19

## 丢弃绑定配置

- 新增变量自动丢弃绑定能力。
- 默认丢弃名为 `_`：
  - 如 `let _ = ...` 可在同一作用域重复绑定，不再触发重复定义错误。
  - 丢弃名不会作为普通变量名参与后续解析。
- 支持通过就近 `flvdiscard` 文件自定义丢弃名：
  - 从源文件目录向上查找。
  - 支持空白/逗号分隔标识符与 `#` 注释。

## 标准库 API 兼容性说明

- `stringlib` 新增 Option 风格查找：
  - `strFindOpt(h, needle, start) -> Option[Int]`
  - 原有 `strFind(...) -> Int` 继续保留（未找到返回 `-1`）。
- `bytelib` 新增：
  - `bytesFindOpt(h, needle, start) -> Option[Int]`
  - 原有 `bytesFind(...) -> Int` 继续保留（未找到返回 `-1`）。
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
- `stdlib/flvrepr` 已改为不直接依赖 `_bridge_python`，改用 `stringlib`/`collections.list` 组合实现。
- `stdlib/httplib.core` 已改为连接复用 `stringlib`、`bytelib`、`asciilib` 的共享能力（find/trim/ascii 转换）。
- 新增 stdlib 跨模块重复定义检测与报告：
  - `scripts/stdlib_duplicate_defs.py`
  - `docs/stdlib_duplicate_defs.md`
- 新增重复策略白名单与归属表：
  - `docs/stdlib_duplicate_allowlist.json`
  - `docs/stdlib_api_ownership.md`
- CI 重复策略改为仅对“未批准”的公开重复失败：
  - 默认排除内部模块（`_bridge_python`、`testns.*`），
  - `file`/`fslib` 的兼容性重名通过白名单显式追踪。

## 标准库扩展（Phase 2 启动）

- 新增 `datetime` 标准库模块（纯 Flavent 实现）：
  - `parseDate` / `parseTime` / `parseDateTime`
  - `formatDate` / `formatTime` / `formatDateTime`
  - `Date` / `Time` / `DateTime` 结构与有效性检查
- 新增 `path` 标准库模块（纯 Flavent 实现）：
  - `pathNormalize` / `pathJoin` / `pathJoinAll`
  - `pathBase` / `pathDir` / `pathExt` / `pathStem`
- 新增 `csv` 标准库模块（纯 Flavent 实现）：
  - `csvParseLine` / `csvParse`
  - `csvStringifyLine` / `csvStringify`
  - 通过 `CsvOptions` 配置分隔符与引用符
- 新增 `url` 标准库模块（纯 Flavent 实现）：
  - `encodeComponent` / `decodeComponent`
  - `queryEncode` / `queryDecode`
  - `queryParse` / `queryBuild`
- 已补充 EN/ZH 文档与索引入口：
  - `docs/en/stdlib/datetime.md`
  - `docs/zh/stdlib/datetime.md`
  - `docs/en/stdlib/path.md`
  - `docs/zh/stdlib/path.md`
  - `docs/en/stdlib/csv.md`
  - `docs/zh/stdlib/csv.md`
  - `docs/en/stdlib/url.md`
  - `docs/zh/stdlib/url.md`

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
  - 新增 sector mixin hook 语法：
    - `hook head|tail|invoke fn ... with(...) = ...`
    - 支持 `id`、`priority`、`depends`、`at`、`cancelable`、`returnDep`、`const` 等选项。
  - resolver 支持基于优先级与依赖的 hook 调用栈解析，并支持 `at` 定位检查。
  - 补强了 hook 语义校验：
    - 未知 `with(...)` 选项键会报错，
    - `head + cancelable=true` 需要返回 `Option[targetReturnType]`，
    - `tail + returnDep` 会校验取值范围与前置返回参数类型。
  - 新增 `flvrepr` 标准库包，用于字符串元数据编解码（`encodeFunctionTarget`、`metaGet`、`metaSet`）。
