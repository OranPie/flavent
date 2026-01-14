# `socket`

## Overview
`socket` provides TCP sockets via the host bridge. All fallible operations return `Result[..., Str]`.

Import:
```flavent
use socket
```

## Types
- `Socket`
- `TcpPeer`
- `TcpAccept`

## API (sector `socket`)
- `tcpConnect(host, port) -> Result[Socket, Str]`
- `tcpListen(host, port, backlog) -> Result[Socket, Str]`
- `tcpAccept(listenSock) -> Result[TcpAccept, Str]`
- `sendAll(sock, data) -> Result[Unit, Str]`
- `recvAll(sock, chunk) -> Result[Bytes, Str]`
- `shutdown(sock) -> Result[Unit, Str]`
- `close(sock) -> Result[Unit, Str]`
- `setTimeoutMillis(sock, ms) -> Result[Unit, Str]`

## Notes
- Always `close(sock)`.
- Prefer `sendAll` for request/response protocols.
