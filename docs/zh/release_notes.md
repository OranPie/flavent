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
- 已在 bridge 封装收敛后刷新基线（`2026-02-19`）：
  - bridge 符号总数：`55`（pure `24` + effectful `31`），
  - stdlib 静态 bridge 引用：`66`（覆盖 `12` 个模块，较 `226` / `26` 下降），
  - `tests_flv` 审计 bridge 调用：`562`（pure_call `486`、rpc `66`、call `10`，较 `1711` 下降）。
- 在 `stringlib` 新增可复用的低层字符串封装，并将核心模块（`url`、`path`、`datetime`、`csv`、`cliargs`、`regex`、`httplib.core`、`struct`、`json`、`hashlib.sha256`、`py`、`process`、`file.lines`、`glob`、`uuid`、`base64.core`、`asciilib`、`stringfmt`）迁移到该封装，降低对 bridge 的直接耦合。
- `stdlib/flvrepr` 已改为不直接依赖 `_bridge_python`，改用 `stringlib`/`collections.list` 组合实现。
- `stdlib/httplib.core` 已改为连接复用 `stringlib`、`bytelib`、`asciilib` 的共享能力（find/trim/ascii 转换）。
- 新增 stdlib 跨模块重复定义检测与报告：
  - `scripts/stdlib_duplicate_defs.py`
  - `docs/stdlib_duplicate_defs.md`
- 新增重复策略白名单与归属表：
  - `docs/stdlib_duplicate_allowlist.json`
  - `docs/stdlib_api_ownership.md`
- 新增 bridge 直连导入边界策略工具：
  - `scripts/stdlib_bridge_boundary.py`
  - `docs/stdlib_bridge_boundary_allowlist.json`
  - CI 现同时校验未批准 bridge 导入模块与白名单陈旧项。
- 改进 check 报告与 warning 策略能力：
  - 新增结构化报告输出：`flavent check ... --report-json <path>`
  - 新增 warning 控制参数：`--warn-as-error`、`--warn-code-as-error`、`--suppress-warning`、`--max-warnings`
  - warning 现提供稳定编码元数据（`WBR001`），便于 CI 与策略自动化。
- 将 stdlib 策略工具 JSON 输出统一到结构化报告 schema（`schema_version: 1.0`）：
  - `scripts/bridge_usage_snapshot.py`
  - `scripts/stdlib_duplicate_defs.py`
  - `scripts/stdlib_bridge_boundary.py`
  - 原始业务载荷现在统一放在 `artifacts.<tool_name>` 下，便于稳定机读。
- 新增 warning 编码目录文档：
  - `docs/warning_catalog.md`
  - `docs/zh/warning_catalog.md`
- 新增 warning baseline gate 工具并接入 CI：
  - `scripts/warning_policy_gate.py`
  - baseline 文件：`docs/warning_baseline.json`
  - CI 现对 stdlib 策略报告执行 `--fail-on-new` warning 策略校验。
- CI 重复策略改为仅对“未批准”的公开重复失败：
  - 默认排除内部模块（`_bridge_python`、`testns.*`），
  - `file`/`fslib` 的兼容性重名通过白名单显式追踪。

## 标准库扩展（Phase 2 启动）

- 新增 `env` 标准库模块（`Result` 风格环境变量接口）：
  - `envGet` / `envGetOr` / `envSet` / `envUnset`
  - `envHas` / `envList` / `envClear`
  - 提供显式且确定性的 `Env` 状态值（通过 `envEmpty` 初始化）
- 新增 `process` 标准库模块（结构化 process 模拟 API）：
  - 规格构建：`processSpec`、`processWith*`
  - 生命周期：`processSpawn`、`processStart`、`processWait`、`processRun`
  - 通过 `ProcessError { code, message }` 返回结构化错误
- 新增 `cliargs` 标准库模块（确定性 argv 解析）：
  - `cliParse`、`cliHasFlag`、`cliGetOption`、`cliPositionals`
  - 支持长参数、短参数组合与 `--` 终止符
- 新增 `log` 标准库模块（分级控制台日志）：
  - 提供 `logLevel*` 等级与可配置 `Logger`（`logDefault`、`logNamed`）
  - 纯函数辅助：`logShouldEmit`、`logRecord`、`logFormat`、`logPrepare`
  - `sector log` 输出函数：`logInfo`、`logWarn`、`logError` 等
- 新增 `collections.deque` 标准库模块（并提供 `deque` 兼容 wrapper）：
  - `dequePushFront` / `dequePushBack`
  - `dequePopFront` / `dequePopBack`
  - `dequePeekFront` / `dequePeekBack` 与列表互转辅助
- 新增 `collections.stack` 标准库模块（并提供 `stack` 兼容 wrapper）：
  - `stackPush` / `stackPop` / `stackPeek`
  - `stackPushAll`、`stackToList`、`stackFromList`
  - 默认值辅助：`stackPeekOr` / `stackPopOr`
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
  - `docs/en/stdlib/env.md`
  - `docs/zh/stdlib/env.md`
  - `docs/en/stdlib/process.md`
  - `docs/zh/stdlib/process.md`
  - `docs/en/stdlib/cliargs.md`
  - `docs/zh/stdlib/cliargs.md`
  - `docs/en/stdlib/log.md`
  - `docs/zh/stdlib/log.md`
  - `docs/en/stdlib/collections.deque.md`
  - `docs/zh/stdlib/collections.deque.md`
  - `docs/en/stdlib/deque.md`
  - `docs/zh/stdlib/deque.md`
  - `docs/en/stdlib/collections.stack.md`
  - `docs/zh/stdlib/collections.stack.md`
  - `docs/en/stdlib/stack.md`
  - `docs/zh/stdlib/stack.md`
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
