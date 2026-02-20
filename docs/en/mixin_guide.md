# Mixin Guide

Date: 2026-02-20

This guide explains practical mixin usage patterns for Flavent.

## 1) Targets and Item Kinds

Mixins can target:
- `sector <Name>`: weave behavior into sector functions.
- `type <Name>`: extend record-like types (fields + methods + method hooks).

Supported items:
- `fn ...` (add function/method)
- `around fn ...` (around weaving)
- `hook head|invoke|tail fn ... with(...) = ...`
- `pattern ...`
- type-target only: `fieldName: Type`

## 2) Hook Points

- `head`: runs before target call.
- `invoke`: full interception (`proceed(...)`).
- `tail`: runs after target call.

Useful options:
- `id`, `priority`, `depends`, `at`
- `cancelable` (`head` only; returns `Option[T]`)
- `returnDep` (`tail` only: `none|use_return|replace_return`)
- `conflict` (`error|prefer|drop`)
- `strict` (`true|false`)

## 3) Conflict and Strict Policies

Duplicate `id` handling:
- `conflict=error` (default): resolve fails.
- `conflict=prefer`: keep highest priority (stable declaration-order tie break).
- `conflict=drop`: drop duplicate-id hooks.

Dependency/locator handling:
- `strict=true` (default): unresolved dependency or locator mismatch fails resolve.
- `strict=false`: hook is dropped and reported.

## 4) Type-Target Hooking

Type-target hook/around names map to mixin-injected methods:

```flv
mixin M v1 into type User:
  fn score(self: User) -> Int = self.id + 1
  hook tail fn score(self: User, ret: Int) -> Int with(returnDep="replace_return") = ret + 10
```

## 5) Reporting and CI Policy

Use:
- `flavent check file.flv --report-json report.json`

`artifacts.mixin_hook_plan` includes resolved active/dropped hook entries with depth, status, and drop reasons.

Warning codes for dropped hooks:
- `WMIX001` duplicate drop
- `WMIX002` unknown dependency drop (non-strict)
- `WMIX003` locator mismatch drop (non-strict)

You can enforce policy with:
- `--warn-code-as-error WMIX002`
- `--suppress-warning WMIX002`
