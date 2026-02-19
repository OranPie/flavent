# `env`

## 概述
提供带 `Result` 错误通道的环境变量风格键值接口。

该模块提供确定性的 env 状态值：
- 按 key 读取/写入字符串值。
- 列举全部键值对。
- 删除 key 或整体清空。

## 导入
```flavent
use env
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Env = Map[Str, Str]
type EnvVar = { key: Str, value: Str }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn envEmpty() -> Env = mapEmpty()
fn envGet(state: Env, key: Str) -> Result[Option[Str], Str] = Ok(mapGet(state, key))
fn envGetOr(state: Env, key: Str, default: Str) -> Result[Str, Str] = Ok(mapGetOr(state, key, default))
fn envSet(state: Env, key: Str, value: Str) -> Result[Env, Str] = Ok(mapPut(state, key, value))
fn envUnset(state: Env, key: Str) -> Result[Env, Str] = Ok(mapRemove(state, key))
fn envHas(state: Env, key: Str) -> Result[Bool, Str] = Ok(mapHasKey(state, key))
fn envList(state: Env) -> Result[List[EnvVar], Str] = Ok(_envVarsFromMapEntries(mapToList(state)))
fn envClear(state: Env) -> Result[Env, Str] = Ok(mapEmpty())
```
<!-- AUTO-GEN:END FUNCTIONS -->
