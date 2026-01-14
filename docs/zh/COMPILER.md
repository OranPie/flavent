# Flavent 编译器与执行流程（中文）

本文档描述 Flavent 从源码到执行的完整流水线。

## 1. 总览

典型流程：
1. **词法分析（Lexing）**：`lexer.py`
2. **语法解析（Parsing）**：`parser.py` → AST
3. **符号解析（Resolution）**：`resolve.py` → 处理 `use`、分配 SymbolId
4. **降级（Lowering）**：`lower.py` → HIR
5. **类型检查（Typechecking）**：`typecheck.py`
6. **运行时（Runtime）**：`runtime.py`（HIR 解释执行 + 事件循环）

## 2. 关键点

- Flavent 将“符号解析”和“类型检查”显式分离。
- `use` 展开是 DFS，并会检测循环依赖。
- `_bridge_python` 是内部能力边界：用户代码不能直接 `use _bridge_python`。
- v2 Python adapter 使用子进程协议：Flavent 侧只通过一个受控入口调用。
