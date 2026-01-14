# `socket.types`

## Overview
Socket-related type definitions and small helpers.

## Import
```flavent
use socket.types
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Socket = Int
type TcpPeer = BridgeSockPeer
type TcpAccept = BridgeSockAccept
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn tcpPeer(host: Str, port: Int) -> TcpPeer = { host = host, port = port }
```
<!-- AUTO-GEN:END FUNCTIONS -->
