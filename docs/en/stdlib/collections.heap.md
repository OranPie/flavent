# `collections.heap`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use collections.heap
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Heap = Empty | Node(Int, Heap, Heap)
type HeapPop = { value: Int, rest: Heap }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
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
<!-- AUTO-GEN:END FUNCTIONS -->
