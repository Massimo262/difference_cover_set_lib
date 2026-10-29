"""A set supporting insert, delete, and 'k-th smallest in [l, r]' queries.

Uses a flat bucket structure. With B buckets holding roughly B keys each, the
total work is proportional to the number of keys visited while walking a
range, which is O(sqrt(N)) plus the cost of the predecessor walks that set the
starting point. Block rebalancing is amortized, so a sequence of mixed
operations stays well-behaved under the same bound.
"""

from __future__ import annotations


class _Block:
    """A sorted slice of keys covering a half-open value range.

    Storing blocks as plain Python lists (kept sorted via ``bisect.insort``
    and list deletion) is the simplest choice that needs no third-party code.
    For the sizes we target per block the cost of a linear shift on update is
    a small constant and stays within the overall O(sqrt(N)) envelope for a
    single operation when block size is governed by ``_rebalance``.
    """

    __slots__ = ("lo", "hi", "keys")

    def __init__(self, lo: int, hi: int) -> None:
        self.lo = lo
        self.hi = hi
        self.keys: list[int] = []


class DifferenceCoverSet:
    """Maintain a dynamic set of integers and answer rank-style range queries.

    The query ``kth_smallest_in_range(l, r, k)`` returns the k-th smallest
    key (1-indexed) among keys in the inclusive range ``[l, r]``. ``insert``
    and ``delete`` return ``True`` when they change the set and ``False``
    otherwise.
    """

    def __init__(self, universe: int = 1 << 20) -> None:
        if universe < 1:
            raise ValueError("universe must be positive")
        # Bucket count: roughly sqrt(universe), which keeps per-block work
        # and per-query block scanning both around O(sqrt(N)).
        nb = max(1, int(universe**0.5))
        span = (universe + nb - 1) // nb
        blocks: list[_Block] = []
        lo = 0
        for _ in range(nb):
            hi = min(universe, lo + span)
            blocks.append(_Block(lo, hi))
            lo = hi
            if lo >= universe:
                break
        self._blocks = blocks
        self._size = 0
        self._max_key = universe - 1

    def __len__(self) -> int:
        return self._size

    def _block_index(self, key: int) -> int:
        # ``bisect`` is avoided here because block edges are precomputed; a
        # direct scan over ``self._blocks`` is at most O(sqrt(N)) entries.
        for i, b in enumerate(self._blocks):
            if b.lo <= key < b.hi:
                return i
        if key < 0:
            raise ValueError("key must be non-negative")
        raise ValueError(f"key {key} outside universe 0..{self._max_key}")

    def insert(self, key: int) -> bool:
        """Add ``key`` to the set. Return ``True`` if newly inserted."""
        if key < 0 or key > self._max_key:
            raise ValueError(f"key {key} outside universe 0..{self._max_key}")
        b = self._blocks[self._block_index(key)]
        lo, hi = 0, len(b.keys)
        while lo < hi:
            mid = (lo + hi) // 2
            if b.keys[mid] < key:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(b.keys) and b.keys[lo] == key:
            return False
        b.keys.insert(lo, key)
        self._size += 1
        self._maybe_rebalance()
        return True

    def delete(self, key: int) -> bool:
        """Remove ``key`` from the set. Return ``True`` if it was present."""
        if key < 0 or key > self._max_key:
            raise ValueError(f"key {key} outside universe 0..{self._max_key}")
        b = self._blocks[self._block_index(key)]
        lo, hi = 0, len(b.keys)
        while lo < hi:
            mid = (lo + hi) // 2
            if b.keys[mid] < key:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(b.keys) and b.keys[lo] == key:
            del b.keys[lo]
            self._size -= 1
            return True
        return False

    def contains(self, key: int) -> bool:
        """Return ``True`` if ``key`` is currently in the set."""
        if key < 0 or key > self._max_key:
            return False
        b = self._blocks[self._block_index(key)]
        lo, hi = 0, len(b.keys)
        while lo < hi:
            mid = (lo + hi) // 2
            if b.keys[mid] < key:
                lo = mid + 1
            else:
                hi = mid
        return lo < len(b.keys) and b.keys[lo] == key

    def _maybe_rebalance(self) -> None:
        """Split oversized blocks so per-block linear scans stay bounded."""
        threshold = max(64, int((len(self._blocks)) * 2))
        # Triggered when a single block grows past the threshold; we insert a
        # new empty neighbor and migrate roughly half the keys into it. The
        # cost is linear in the block, but it is amortized across inserts.
        i = 0
        while i < len(self._blocks):
            b = self._blocks[i]
            if len(b.keys) <= threshold:
                i += 1
                continue
            mid = (b.lo + b.hi) // 2
            if mid <= b.lo:
                # Block too narrow to halve at the current resolution; leave
                # it as-is rather than spin forever on tiny value ranges.
                i += 1
                continue
            left = _Block(b.lo, mid)
            right = _Block(mid, b.hi)
            for k in b.keys:
                if k < mid:
                    left.keys.append(k)
                else:
                    right.keys.append(k)
            self._blocks[i:i + 1] = [left, right]
            i += 2

    def kth_smallest_in_range(self, l: int, r: int, k: int) -> int:
        """Return the k-th smallest key among those in the inclusive range [l, r].

        k is 1-indexed: ``k == 1`` asks for the smallest key in the range.
        Raises ``ValueError`` when the range is invalid or fewer than k keys
        fall in the range.
        """
        if k < 1:
            raise ValueError("k must be at least 1")
        if l > r:
            raise ValueError("range lower bound exceeds upper bound")
        if l < 0 or r > self._max_key:
            raise ValueError(
                f"range [{l}, {r}] outside universe 0..{self._max_key}"
            )
        remaining = k
        for b in self._blocks:
            # Skip blocks that do not overlap [l, r] at all.
            if b.hi <= l or b.lo > r:
                continue
            lo = 0
            hi = len(b.keys)
            while lo < hi:
                mid = (lo + hi) // 2
                if b.keys[mid] < l:
                    lo = mid + 1
                else:
                    hi = mid
            start = lo
            # Find the first key strictly greater than r.
            lo2 = start
            hi2 = len(b.keys)
            while lo2 < hi2:
                mid = (lo2 + hi2) // 2
                if b.keys[mid] <= r:
                    lo2 = mid + 1
                else:
                    hi2 = mid
            end = lo2
            available = end - start
            if remaining <= available:
                return b.keys[start + remaining - 1]
            remaining -= available
        raise ValueError(
            f"fewer than {k} keys in range [{l}, {r}]"
        )
