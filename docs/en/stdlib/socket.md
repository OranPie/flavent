# `socket`

## Overview
TCP sockets via the host bridge.

Treat `socket` as the umbrella module. The actual definitions live in:
- `socket.types`
- `socket.api`

This page focuses on usage patterns and pitfalls. The API signature blocks below are maintained by `scripts/docgen_stdlib.py`.

## Import
```flavent
use socket
```

## Common patterns

### Connect + sendAll + recvAll

```flavent
use socket

type Event.Start = {}

sector main:
  on Event.Start -> do:
    let s = rpc socket.tcpConnect("127.0.0.1", 8080)?
    rpc socket.sendAll(s, b"hello")?
    let resp = rpc socket.recvAll(s, 4096)?
    rpc socket.close(s)
    resp
    stop()
```

## Notes
- Always try to `close(s)` on both success and error paths.
- `recvAll` reads until the peer closes the connection (empty bytes).
- Use `setTimeoutMillis` to avoid blocking indefinitely.

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
```
<!-- AUTO-GEN:END FUNCTIONS -->
