# `consoleIO`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use consoleIO
```

## 函数
```flavent
fn print(s: Str) -> Unit = call _bridge_python.consolePrint(s)
fn println(s: Str) -> Unit = call _bridge_python.consolePrintln(s)
fn printErr(s: Str) -> Unit = call _bridge_python.consolePrintErr(s)
fn printlnErr(s: Str) -> Unit = call _bridge_python.consolePrintlnErr(s)
fn readLine() -> Str = rpc _bridge_python.consoleReadLine()
fn flush() -> Unit = call _bridge_python.consoleFlush()
```

