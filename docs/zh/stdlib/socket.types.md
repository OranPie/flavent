# `socket.types`

## 概述
socket 的类型定义（以及 peer helper）。

## 导入
```flavent
use socket.types
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Socket = Int
type TcpPeer = BridgeSockPeer
type TcpAccept = BridgeSockAccept
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn tcpPeer(host: Str, port: Int) -> TcpPeer = { host = host, port = port }
```
<!-- AUTO-GEN:END FUNCTIONS -->

