# Warning 编码目录

本文档定义用于报告与 CI 策略的稳定 warning/error 编码。

## `flavent check`

- `WBR001`（`warning`，阶段 `bridge_audit`）
  - bridge 审计检测到已弃用 bridge shim。
  - 支持抑制（`--suppress-warning WBR001`）与升级为错误（`--warn-code-as-error WBR001`）。
- `ECHECKWARN`（`error`，阶段 `check`）
  - warning 策略触发失败时产生（`--strict`、`--warn-as-error`、`--warn-code-as-error`、`--max-warnings`）。

## stdlib 策略脚本

- `ESTDLIBDUP001`（`error`，阶段 `stdlib_duplicate_defs`）
  - 检测到未批准的 stdlib 跨模块重复定义。
- `WSTDLIBDUP001`（`warning`，阶段 `stdlib_duplicate_defs`）
  - 重复定义白名单存在陈旧条目。
- `ESTDLIBBRIDGE001`（`error`，阶段 `stdlib_bridge_boundary`）
  - 检测到未批准的 stdlib 直接 `_bridge_python` 导入。
- `WSTDLIBBRIDGE001`（`warning`，阶段 `stdlib_bridge_boundary`）
  - bridge 边界白名单存在陈旧条目。

## 策略建议

- 通过 `--warn-code-as-error` 逐步收紧指定 warning。
- `--suppress-warning` 仅在有迁移说明的前提下临时使用。
- 目标是将 warning 降到零，抑制项应视为待清理技术债。
- CI 无新增 warning gate（策略报告）：
  - baseline 文件：`docs/warning_baseline.json`
  - 命令：
    - `python3 scripts/warning_policy_gate.py --baseline docs/warning_baseline.json --reports <report1.json> <report2.json> --fail-on-new`
