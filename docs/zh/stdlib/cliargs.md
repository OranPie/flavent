# `cliargs`

## 概述
用于列表输入 argv 的确定性命令行参数解析器。

支持：
- 长参数：`--verbose`、`--port=8080`、`--port 8080`
- 短参数组合：`-abc` => `a`、`b`、`c`
- 位置参数与 `--` 终止符

## 导入
```flavent
use cliargs
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type CliArgs = {
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn cliEmpty() -> CliArgs = { flags = setEmpty(), options = mapEmpty(), positionals = Nil, raw = Nil }
fn cliParse(argv: List[Str]) -> Result[CliArgs, Str] = _parseAcc(argv, false, setEmpty(), mapEmpty(), Nil, Nil)
fn cliHasFlag(args: CliArgs, name: Str) -> Bool = setHas(args.flags, name)
fn cliGetOption(args: CliArgs, key: Str) -> Option[Str] = mapGet(args.options, key)
fn cliGetOptionOr(args: CliArgs, key: Str, default: Str) -> Str = mapGetOr(args.options, key, default)
fn cliPositionals(args: CliArgs) -> List[Str] = args.positionals
fn cliRaw(args: CliArgs) -> List[Str] = args.raw
```
<!-- AUTO-GEN:END FUNCTIONS -->
