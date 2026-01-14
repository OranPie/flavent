# `math`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use math
```

## 函数
```flavent
fn minInt(a: Int, b: Int) -> Int = match a <= b:
fn maxInt(a: Int, b: Int) -> Int = match a <= b:
fn absInt(x: Int) -> Int = match x < 0:
fn clampInt(x: Int, lo: Int, hi: Int) -> Int = maxInt(lo, minInt(x, hi))
fn signInt(x: Int) -> Int = match x < 0:
fn isEven(x: Int) -> Bool = ((x / 2) * 2) == x
fn isOdd(x: Int) -> Bool = match isEven(x):
fn min3Int(a: Int, b: Int, c: Int) -> Int = minInt(minInt(a, b), c)
fn max3Int(a: Int, b: Int, c: Int) -> Int = maxInt(maxInt(a, b), c)
fn gcdInt(a: Int, b: Int) -> Int = do:
fn lcmInt(a: Int, b: Int) -> Int = do:
fn minFloat(a: Float, b: Float) -> Float = match a <= b:
fn maxFloat(a: Float, b: Float) -> Float = match a <= b:
fn absFloat(x: Float) -> Float = match x < 0.0:
fn clampFloat(x: Float, lo: Float, hi: Float) -> Float = maxFloat(lo, minFloat(x, hi))
fn pi() -> Float = 3.141592653589793
fn tau() -> Float = 6.283185307179586
fn halfPi() -> Float = 1.5707963267948966
fn ln10() -> Float = 2.302585092994046
fn normAngle(x: Float) -> Float = _normAngle(x, 0.0)
fn sin(x: Float) -> Float = do:
fn cos(x: Float) -> Float = do:
fn tan(x: Float) -> Float = do:
fn exp(x: Float) -> Float = _expSeries(x, 1.0, 1.0, 1.0)
fn ln(x: Float) -> Float = match x <= 0.0:
fn log10(x: Float) -> Float = ln(x) / ln10()
fn log(x: Float, base: Float) -> Float = ln(x) / ln(base)
fn sqrt(x: Float) -> Float = match x <= 0.0:
fn atan(x: Float) -> Float = match absFloat(x) > 1.0:
fn atan2(y: Float, x: Float) -> Float = match x == 0.0:
```

