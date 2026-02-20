# Mixin Hooks and `flvrepr`

Date: 2026-02-19

This document describes the hook-oriented mixin extension and the `flvrepr` metadata helper package.

## Hook Syntax

Inside a sector-target or type-target mixin:

```flv
hook <point> fn <target>(<params>) -> <ret>
  with(id="...", priority=10, depends="A,B", at="anchor:foo", ...)
= <expr-or-do>
```

Hook points:
- `head`: runs before target invocation.
- `tail`: runs after target invocation.
- `invoke`: full around-style interception (`proceed(...)` supported).

For type-target mixins, `hook`/`around` targets are method names declared by type mixins (`fn method(self: Type, ...)`).

## Hook Options

- `id`: unique hook id within the target function stack.
- `priority`: higher value has stronger precedence in call stack ordering.
- `depends`: comma-separated hook ids that must run before this hook.
- `at`: locator (`anchor:<fn>` or `line:<n>` / `line:<n>#<fn>`).
- `cancelable` (head only): hook returns `Option[T]`; `Some(v)` short-circuits target with `v`, `None` continues.
- `returnDep` (tail only):
  - `none` (default)
  - `use_return`: hook receives prior return as extra arg but final return stays original.
  - `replace_return`: hook receives prior return as extra arg and its result becomes final return.
- `const` / `constParams` / `constArgs`: comma-separated constant strings appended to hook call arguments.
- `conflict`: duplicate hook-id policy (`error` default, `prefer`, `drop`).
- `strict`: dependency/locator enforcement policy (`true` default).
- Unknown option keys are rejected during resolve.
- `conflict` validation rules:
  - `error`: duplicate hook id in same target fails resolve.
  - `prefer`: keeps the highest-priority duplicate (stable declaration-order tie break).
  - `drop`: drops duplicate candidates for that hook id.
- `strict` behavior:
  - `true`: unresolved `depends` or locator mismatch fails resolve.
  - `false`: unresolved `depends` or locator mismatch drops that hook from the resolved stack.
- Validation rules:
  - `head + cancelable=true` requires return type `Option[targetReturnType]`.
  - `tail + returnDep in {use_return, replace_return}` requires an extra `ret`-style parameter typed as target return type.
  - `tail + returnDep="replace_return"` must return the target return type.

## Call Stack Resolver

Per target function, hooks are resolved by:
1. dependency graph (`depends`)
2. priority (higher first among ready nodes)
3. stable declaration order as tie-break

Execution stack shape:
- outer: `head` hooks
- middle: `invoke` hooks
- inner: `tail` hooks (arranged so tail post-phase remains priority-aware)

## Hook Plan Reporting

`flavent check --report-json <path>` now includes `artifacts.mixin_hook_plan` when mixins are used.

Each entry includes:
- `owner_kind` (`sector` or `type`)
- `target` (`Owner.fn` / `Type.method`)
- `hook_id`, `point`, `origin`, `conflict_policy`, `mixin_key`
- `priority`, `depends`, `at`, `depth` (`0` is outermost for active hooks)
- `status`: `active` or `dropped`
- `drop_reason` (when dropped): `duplicate_drop`, `unknown_dependency:<id>`, `locator_mismatch`

## `flvrepr` Package

`stdlib/flvrepr` provides lightweight string metadata encoding/decoding for hook/function target metadata.

Key APIs:
- `encodePairs(List[MetaPair]) -> Str`
- `decodePairs(Str) -> List[MetaPair]`
- `metaGet(meta, key) -> Option[Str]`
- `metaSet(meta, key, value) -> Str`
- `encodeFunctionTarget(target, point, priority, at) -> Str`

Example:

```flv
use flvrepr

let meta = encodeFunctionTarget("S.base", "invoke", "10", "anchor:base")
let p = metaGet(meta, "priority")      // Some("10")
let meta2 = metaSet(meta, "priority", "20")
```
