# Mixin 能力扩展计划（下一阶段）

日期：2026-02-20

本计划在现有 sector hook 基础上继续扩展 mixin 能力。

## 当前文档状态（已确认）

- [x] 已有核心 hook 设计文档：`docs/mixin_hooks.md`
- [x] 语法参考已覆盖 mixin/hook：`docs/grammar_ebnf.md`
- [x] 发布说明已记录已实现 hook 能力：`docs/release_notes.md`
- [x] 示例已覆盖基础 hook/mixin：
  - `examples/19_mixin_hook_chain.flv`
  - `examples/20_mixin_cancelable_override.flv`
- [~] 仍缺少 EN/ZH 面向用户的专门 mixin 使用指南页
- [~] 仍缺少“mixin 诊断码目录”文档

## 目标

提供可组合、可调试、可策略化治理的 mixin 系统，并补齐诊断与文档。

## Phase A：Hook 目标覆盖扩展

- [x] 为 type-target mixin 增加 `hook` 支持（当前以 sector 为主）。
- [ ] 明确 callable 目标边界（sector fn / type method / handler）。
- [ ] 统一既有 `around fn` 与新 hook 的兼容规则。
- [~] 测试：
  - [x] type-target invoke/head/tail 正向用例
  - [x] 非支持目标的精确报错用例

## Phase B：Hook 上下文与控制策略

- [ ] 增加结构化 hook 上下文字段（hook id、target、point、调用深度）。
- [x] 增加冲突策略（`error` / `prefer` / `drop`）。
- [x] 增加 strict 模式：未解析 `depends` 或 locator 失配直接失败。
- [~] 增加 hook 栈“dry-run resolve”输出（CI/排障）。（已增加 JSON 报告产物）
- [ ] 测试：
  - [x] 冲突策略行为矩阵
  - [x] strict / non-strict 差异行为

## Phase C：诊断与报告

- [ ] 引入稳定 mixin 诊断码（如 `WMIX*`、`EMIX*`）。
- [ ] 在 `flavent check --report-json` 中输出 hook 栈与 mixin 诊断信息。
- [ ] 与现有 warning 策略对齐（抑制/升级/门禁）。
- [ ] 测试：
  - [ ] 诊断码与 stage 元数据
  - [ ] 升级/抑制流程

## Phase D：文档与示例补齐

- [ ] 新增 EN 指南：`docs/en/mixin_guide.md`
- [ ] 新增 ZH 指南：`docs/zh/mixin_guide.md`
- [ ] 新增 mixin 诊断码目录页。
- [ ] 新增 6+ 个专项示例：
  - [ ] type-target hook 链
  - [x] 冲突策略演示
  - [x] strict locator/depends 校验
  - [ ] 报告与 CI 策略接入示例

## 完成标准

- [ ] `tests`、`tests_flv`、examples check 全绿。
- [ ] EN/ZH mixin 指南可直接用于迁移与新开发。
- [ ] 结构化报告包含稳定 mixin 诊断码。
- [ ] CI 可执行“无新增 mixin warning”策略。
