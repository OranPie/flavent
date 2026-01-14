# `consoleIO`

## 概述
通过宿主桥（host bridge）进行终端输入输出。

导入：
```flavent
use consoleIO
```

## API
- `print(s: Str) -> Unit`
- `println(s: Str) -> Unit`
- `printErr(s: Str) -> Unit`
- `printlnErr(s: Str) -> Unit`
- `readLine() -> Str`
- `flush() -> Unit`
