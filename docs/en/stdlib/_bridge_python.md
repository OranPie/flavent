# `_bridge_python`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use _bridge_python
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type BridgeSockPeer = { host: Str, port: Int }
type BridgeSockAccept = { sock: Int, peer: BridgeSockPeer }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn strLen(s: Str) -> Int = 0
fn strCodeAt(s: Str, i: Int) -> Int = 0
fn strSlice(s: Str, start: Int, end: Int) -> Str = ""
fn strFromCode(code: Int) -> Str = ""
fn strToFloat(s: Str) -> Float = 0.0
fn floatToStr(x: Float) -> Str = ""
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
<!-- AUTO-GEN:END FUNCTIONS -->
