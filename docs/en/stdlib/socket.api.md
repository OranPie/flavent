# `socket.api`

## Overview
Effectful socket operations (`sector socket`).

Guidance:
- `send/recv` are single syscalls.
- `sendAll/recvAll` are convenience wrappers:
  - `sendAll` loops until all bytes are written.
  - `recvAll` loops until the peer closes the connection.
- `setTimeoutMillis` controls blocking behavior.

## Import
```flavent
use socket.api
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
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
