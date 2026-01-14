# `_bridge_python`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use _bridge_python
```

## 类型
```flavent
type BridgeSockPeer = { host: Str, port: Int }
type BridgeSockAccept = { sock: Int, peer: BridgeSockPeer }
```

## 函数
```flavent
fn strLen(s: Str) -> Int = 0
fn strCodeAt(s: Str, i: Int) -> Int = 0
fn strSlice(s: Str, start: Int, end: Int) -> Str = ""
fn strFromCode(code: Int) -> Str = ""
fn nowMillis() -> Int = 0
fn nowNanos() -> Int = 0
fn monoMillis() -> Int = 0
fn monoNanos() -> Int = 0
fn sleep(ms: Int) -> Unit = ()
fn fsReadFileBytes(path: Str) -> Result[Bytes, Str] = Err("")
fn fsReadFileStr(path: Str) -> Result[Str, Str] = Err("")
fn fsWriteFileBytes(path: Str, data: Bytes) -> Result[Unit, Str] = Err("")
fn fsWriteFileStr(path: Str, data: Str) -> Result[Unit, Str] = Err("")
fn fsListDir(path: Str) -> Result[List[Str], Str] = Err("")
fn fsExists(path: Str) -> Result[Bool, Str] = Err("")
fn fsMkdirs(path: Str) -> Result[Unit, Str] = Err("")
fn fsRemove(path: Str) -> Result[Unit, Str] = Err("")
fn fsTempFile(prefix: Str, suffix: Str) -> Result[Str, Str] = Err("")
fn fsTempDir(prefix: Str) -> Result[Str, Str] = Err("")
fn uuid4Bytes() -> Bytes = b""
fn consolePrint(s: Str) -> Unit = ()
fn consolePrintln(s: Str) -> Unit = ()
fn consolePrintErr(s: Str) -> Unit = ()
fn consolePrintlnErr(s: Str) -> Unit = ()
fn consoleReadLine() -> Str = ""
fn consoleFlush() -> Unit = ()
fn sockTcpConnect(host: Str, port: Int) -> Result[Int, Str] = Err("")
fn sockTcpListen(host: Str, port: Int, backlog: Int) -> Result[Int, Str] = Err("")
fn sockTcpAccept(s: Int) -> Result[BridgeSockAccept, Str] = Err("")
fn sockSend(s: Int, data: Bytes) -> Result[Int, Str] = Err("")
fn sockRecv(s: Int, n: Int) -> Result[Bytes, Str] = Err("")
fn sockClose(s: Int) -> Result[Unit, Str] = Err("")
fn sockShutdown(s: Int) -> Result[Unit, Str] = Err("")
fn sockSetTimeoutMillis(s: Int, ms: Int) -> Result[Unit, Str] = Err("")
fn pyAdapterCall(adapter: Str, method: Str, payload: Bytes) -> Result[Bytes, Str] = Err("")
```

