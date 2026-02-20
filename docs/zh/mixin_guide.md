# Mixin 使用指南

日期：2026-02-20

本文给出 Flavent mixin 的常用模式与治理建议。

## 1）目标与可用项

Mixin 可作用于：
- `sector <Name>`：对 sector 函数织入行为。
- `type <Name>`：扩展记录类型（字段、方法、方法 hook）。

可用项：
- `fn ...`（新增函数/方法）
- `around fn ...`（环绕织入）
- `hook head|invoke|tail fn ... with(...) = ...`
- `pattern ...`
- 仅 type-target：`fieldName: Type`

## 2）Hook 点

- `head`：目标调用前执行。
- `invoke`：完整拦截（支持 `proceed(...)`）。
- `tail`：目标调用后执行。

常用选项：
- `id`、`priority`、`depends`、`at`
- `cancelable`（仅 `head`，返回 `Option[T]`）
- `returnDep`（仅 `tail`：`none|use_return|replace_return`）
- `conflict`（`error|prefer|drop`）
- `strict`（`true|false`）

## 3）冲突与 strict 策略

重复 `id` 的处理：
- `conflict=error`（默认）：直接失败。
- `conflict=prefer`：保留优先级更高者（再用声明顺序稳定决策）。
- `conflict=drop`：重复 id 的候选全部丢弃。

依赖/定位处理：
- `strict=true`（默认）：依赖未解析或 locator 失配会失败。
- `strict=false`：对应 hook 会被丢弃并进入报告。

## 4）Type-Target Hook 示例

type-target 的 hook/around 目标名对应 mixin 注入的方法名：

```flv
mixin M v1 into type User:
  fn score(self: User) -> Int = self.id + 1
  hook tail fn score(self: User, ret: Int) -> Int with(returnDep="replace_return") = ret + 10
```

## 5）报告与 CI 策略

使用：
- `flavent check file.flv --report-json report.json`

`artifacts.mixin_hook_plan` 会输出 hook 栈的 active/dropped 条目、depth、status、drop 原因。

丢弃类 warning 编码：
- `WMIX001`：重复 id 丢弃
- `WMIX002`：非 strict 依赖未解析丢弃
- `WMIX003`：非 strict locator 失配丢弃

可配合策略参数：
- `--warn-code-as-error WMIX002`
- `--suppress-warning WMIX002`
