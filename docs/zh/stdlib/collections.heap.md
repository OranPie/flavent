# `collections.heap`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use collections.heap
```

## 类型
```flavent
type Heap = Empty | Node(Int, Heap, Heap)
type HeapPop = { value: Int, rest: Heap }
```

## 函数
```flavent
fn heapEmpty() -> Heap = Empty
fn heapIsEmpty(h: Heap) -> Bool = match h:
fn heapMerge(a: Heap, b: Heap) -> Heap = match a:
fn heapInsert(x: Int, h: Heap) -> Heap = heapMerge(Node(x, Empty, Empty), h)
fn heapPeek(h: Heap) -> Option[Int] = match h:
fn heapPop(h: Heap) -> Option[HeapPop] = match h:
fn heapPeekOr(h: Heap, default: Int) -> Int = match heapPeek(h):
fn heapPopOr(h: Heap, default: Int) -> HeapPop = match heapPop(h):
fn heapSize(h: Heap) -> Int = match h:
fn heapFromList(xs: List[Int]) -> Heap = match xs:
fn heapInsertAll(xs: List[Int], h: Heap) -> Heap = match xs:
fn heapToSortedList(h: Heap) -> List[Int] = reverse(_heapToListAcc(h, Nil))
fn heapMinOr(h: Heap, default: Int) -> Int = match heapPeek(h):
```

