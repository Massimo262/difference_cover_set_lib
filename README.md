# difference_cover_set_lib

A small Python library that maintains a dynamic set of integers supporting `insert`, `delete`, and a `kth_smallest_in_range(l, r, k)` query. It uses a flat bucket structure with per-block sorted lists, giving O(sqrt(N)) work for each operation when block sizes are kept balanced.

## Usage

```python
from difference_cover_set_lib import DifferenceCoverSet

s = DifferenceCoverSet(1024)
s.insert(10)
s.insert(30)
s.insert(20)
assert s.kth_smallest_in_range(0, 100, 1) == 10
assert s.kth_smallest_in_range(0, 100, 2) == 20
assert s.kth_smallest_in_range(0, 100, 3) == 30
s.delete(20)
assert s.kth_smallest_in_range(0, 100, 2) == 30
```

## Why this exists

When you need to repeatedly ask "what is the k-th smallest value currently in some value window?" over a set that is being mutated between queries, a plain sorted list makes each query linear. This library splits the value universe into roughly sqrt(N) buckets and keeps each bucket sorted, so a range query walks O(sqrt(N)) buckets plus the bucket-local rank work. Updates rebalance only when a block grows past a threshold.

The trade-off: memory overhead from the bucket array and a fixed universe chosen at construction time. The universe is bounded, so all keys must be in `[0, universe)`.

## Edge you will hit

The universe is fixed at construction. Inserting a key outside `[0, universe)` raises `ValueError`. The range query also raises `ValueError` when fewer than `k` keys fall in `[l, r]`, because the only sensible alternative would be returning a sentinel, and callers checking for that sentinel is more error-prone than catching the exception.
