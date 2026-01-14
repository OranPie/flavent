# `struct`

## 概述
二进制打包/解包（兼容 Python struct）。

导入：
```flavent
use struct
```

## API
- `calcsize(fmt: Str) -> Result[Int, Str]`
- `pack(fmt: Str, args: List[Int]) -> Result[Bytes, Str]`
- `unpack(fmt: Str, data: Bytes) -> Result[List[Int], Str]`
- `unpackFrom(fmt: Str, data: Bytes, offset: Int) -> Result[List[Int], Str]`
