# `socket.api`

## 概述
socket 的 effectful API（`sector socket`）。

提示：
- `send/recv` 是一次系统调用语义。
- `sendAll/recvAll` 是便利封装：
  - `sendAll` 会循环发送直到全部写入。
  - `recvAll` 会循环读取直到对端关闭连接（读到空 bytes）。
- 可用 `setTimeoutMillis` 设置读写超时。

## 导入
```flavent
use socket.api
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn tcpConnect(host: Str, port: Int) -> Result[Socket, Str] = rpc _bridge_python.sockTcpConnect(host, port)
fn tcpConnectPeer(peer: TcpPeer) -> Result[Socket, Str] = tcpConnect(peer.host, peer.port)
fn tcpListen(host: Str, port: Int, backlog: Int) -> Result[Socket, Str] = rpc _bridge_python.sockTcpListen(host, port, backlog)
fn tcpListenPeer(peer: TcpPeer, backlog: Int) -> Result[Socket, Str] = tcpListen(peer.host, peer.port, backlog)
fn tcpAccept(s: Socket) -> Result[TcpAccept, Str] = rpc _bridge_python.sockTcpAccept(s)
fn send(s: Socket, data: Bytes) -> Result[Int, Str] = rpc _bridge_python.sockSend(s, data)
fn recv(s: Socket, n: Int) -> Result[Bytes, Str] = rpc _bridge_python.sockRecv(s, n)
fn close(s: Socket) -> Result[Unit, Str] = rpc _bridge_python.sockClose(s)
fn shutdown(s: Socket) -> Result[Unit, Str] = rpc _bridge_python.sockShutdown(s)
fn setTimeoutMillis(s: Socket, ms: Int) -> Result[Unit, Str] = rpc _bridge_python.sockSetTimeoutMillis(s, ms)
fn sendAll(s: Socket, data: Bytes) -> Result[Unit, Str] = do:
fn recvAll(s: Socket, chunk: Int) -> Result[Bytes, Str] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->

