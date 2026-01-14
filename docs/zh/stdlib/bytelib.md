# `bytelib`

## 概述
`Bytes` 的底层操作。

导入：
```flavent
use bytelib
```

## API
- `bytesLen(b) -> Int`
- `bytesGet(b, i) -> Int`
- `bytesSlice(b, start, end) -> Bytes`
- `bytesConcat(a, b) -> Bytes`
- `bytesFromList(xs: List[Int]) -> Bytes`
- `bytesToList(b) -> List[Int]`

搜索辅助：
- `bytesFind(haystack, needle, start) -> Int`
- `bytesStartsWith(haystack, prefix) -> Bool`
- `bytesEndsWith(haystack, suffix) -> Bool`
