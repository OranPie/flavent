# `random`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use random
```

## 类型
```flavent
type Rng = { state: Int }
type RngStepU32 = { value: Int, rng: Rng }
type RngStepInt = { value: Int, rng: Rng }
type RngStepFloat = { value: Float, rng: Rng }
type RngStepBool = { value: Bool, rng: Rng }
type RngShuffleRes[T] = { value: List[T], rng: Rng }
type RngChoiceRes[T] = { value: Result[T, Str], rng: Rng }
type RngBytesRes = { value: Result[Bytes, Str], rng: Rng }
type RngUniformRes = { value: Float, rng: Rng }
type RngSampleRes[T] = { value: Result[List[T], Str], rng: Rng }
```

## 函数
```flavent
fn rngSeed(seed: Int) -> Rng = do:
fn rngNextU32(r: Rng) -> RngStepU32 = do:
fn rngNextInt(r: Rng, lo: Int, hi: Int) -> RngStepInt = do:
fn rngNextFloat01(r: Rng) -> RngStepFloat = do:
fn rngBool(r: Rng) -> RngStepBool = do:
fn rngShuffle[T](r: Rng, xs: List[T]) -> RngShuffleRes[T] = do:
fn rngChoice[T](r: Rng, xs: List[T]) -> RngChoiceRes[T] = do:
fn rngBytes(r: Rng, n: Int) -> RngBytesRes = match n < 0:
fn rngUniform(r: Rng, lo: Float, hi: Float) -> RngUniformRes = do:
fn rngSample[T](r: Rng, xs: List[T], k: Int) -> RngSampleRes[T] = do:
```

