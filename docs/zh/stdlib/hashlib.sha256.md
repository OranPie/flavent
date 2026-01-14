# `hashlib.sha256`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use hashlib.sha256
```

## 函数
```flavent
fn sha256DigestNative(b: Bytes) -> Bytes = do:
fn sha256HexNative(b: Bytes) -> Str = _shaHexAcc(bytesToList(sha256DigestNative(b)), "")
```

