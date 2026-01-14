# `socket`

## 概述
`socket` 通过宿主桥（host bridge）提供 TCP socket。

所有可能失败的操作都返回 `Result[..., Str]`。

导入：
```flavent
use socket
```

## 类型
- `Socket`
- `TcpPeer`
- `TcpAccept`

## API（sector `socket`）
- `tcpConnect(host, port) -> Result[Socket, Str]`
- `tcpListen(host, port, backlog) -> Result[Socket, Str]`
- `tcpAccept(listenSock) -> Result[TcpAccept, Str]`
- `sendAll(sock, data) -> Result[Unit, Str]`
- `recvAll(sock, chunk) -> Result[Bytes, Str]`
- `shutdown(sock) -> Result[Unit, Str]`
- `close(sock) -> Result[Unit, Str]`
- `setTimeoutMillis(sock, ms) -> Result[Unit, Str]`

## 注意
- 使用完必须 `close(sock)`。
- 请求/响应协议（如 HTTP）建议用 `sendAll`。
