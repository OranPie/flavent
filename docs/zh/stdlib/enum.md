# `enum`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use enum
```

## 类型
```flavent
type EnumCase = { name: Str, tag: Int }
type EnumInfo = { cases: List[EnumCase] }
```

## 函数
```flavent
fn enumInfoEmpty() -> EnumInfo = { cases = Nil }
fn enumCase(name: Str, tag: Int) -> EnumCase = { name = name, tag = tag }
fn enumInfoAdd(info: EnumInfo, c: EnumCase) -> EnumInfo = { cases = Cons(c, info.cases) }
fn enumCases(info: EnumInfo) -> List[EnumCase] = info.cases
fn enumNextTag(info: EnumInfo) -> Int = _enMaxTag(info.cases, -1) + 1
fn enumInfoAddAuto(info: EnumInfo, name: Str) -> EnumInfo = do:
fn enumFindByName(info: EnumInfo, name: Str) -> Option[EnumCase] = match info.cases:
fn enumInfoFromNames(names: List[Str]) -> EnumInfo = _enFromNames(names, 0, enumInfoEmpty())
fn enumFindByTag(info: EnumInfo, tag: Int) -> Option[EnumCase] = match info.cases:
fn enumTagByName(info: EnumInfo, name: Str) -> Option[Int] = match enumFindByName(info, name):
fn enumNameByTag(info: EnumInfo, tag: Int) -> Option[Str] = match enumFindByTag(info, tag):
fn enumRequireByName(info: EnumInfo, name: Str) -> Result[EnumCase, Str] = match enumFindByName(info, name):
fn enumRequireByTag(info: EnumInfo, tag: Int) -> Result[EnumCase, Str] = match enumFindByTag(info, tag):
fn enumHasName(info: EnumInfo, name: Str) -> Bool = isSome(enumFindByName(info, name))
fn enumHasTag(info: EnumInfo, tag: Int) -> Bool = isSome(enumFindByTag(info, tag))
fn enumInfoAddChecked(info: EnumInfo, c: EnumCase) -> Result[EnumInfo, Str] = match enumHasName(info, c.name) or enumHasTag(info, c.tag):
fn enumInfoAddAutoChecked(info: EnumInfo, name: Str) -> Result[EnumInfo, Str] = match enumHasName(info, name):
fn enumInfoValidate(info: EnumInfo) -> Result[Unit, Str] = _enumValidateAcc(info.cases, Nil, Nil)
```

