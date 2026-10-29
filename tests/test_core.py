import unittest

from difference_cover_set_lib import DifferenceCoverSet


class TestInsertDelete(unittest.TestCase):
    def test_insert_returns_true_when_new(self):
        s = DifferenceCoverSet(256)
        self.assertTrue(s.insert(5))
        self.assertFalse(s.insert(5))

    def test_delete_returns_true_when_present(self):
        s = DifferenceCoverSet(256)
        s.insert(7)
        self.assertTrue(s.delete(7))
        self.assertFalse(s.delete(7))

    def test_len_tracks_size(self):
        s = DifferenceCoverSet(256)
        self.assertEqual(len(s), 0)
        s.insert(1)
        s.insert(2)
        s.insert(3)
        self.assertEqual(len(s), 3)
        s.delete(2)
        self.assertEqual(len(s), 2)

    def test_contains_after_insert_delete(self):
        s = DifferenceCoverSet(256)
        s.insert(11)
        self.assertTrue(s.contains(11))
        s.delete(11)
        self.assertFalse(s.contains(11))

    def test_insert_out_of_universe_raises(self):
        s = DifferenceCoverSet(16)
        with self.assertRaises(ValueError):
            s.insert(-1)
        with self.assertRaises(ValueError):
            s.insert(16)


class TestKthSmallest(unittest.TestCase):
    def test_single_element_range(self):
        s = DifferenceCoverSet(256)
        s.insert(42)
        self.assertEqual(s.kth_smallest_in_range(0, 255, 1), 42)

    def test_kth_in_dense_range(self):
        s = DifferenceCoverSet(256)
        for x in [10, 20, 30, 40, 50]:
            s.insert(x)
        self.assertEqual(s.kth_smallest_in_range(0, 100, 1), 10)
        self.assertEqual(s.kth_smallest_in_range(0, 100, 3), 30)
        self.assertEqual(s.kth_smallest_in_range(15, 45, 2), 30)

    def test_kth_with_empty_range_contents(self):
        s = DifferenceCoverSet(256)
        s.insert(5)
        s.insert(6)
        with self.assertRaises(ValueError):
            s.kth_smallest_in_range(7, 8, 1)

    def test_kth_k_too_large_raises(self):
        s = DifferenceCoverSet(256)
        s.insert(1)
        s.insert(2)
        with self.assertRaises(ValueError):
            s.kth_smallest_in_range(0, 255, 3)

    def test_kth_k_invalid(self):
        s = DifferenceCoverSet(256)
        with self.assertRaises(ValueError):
            s.kth_smallest_in_range(0, 255, 0)

    def test_kth_range_invalid(self):
        s = DifferenceCoverSet(256)
        with self.assertRaises(ValueError):
            s.kth_smallest_in_range(10, 5, 1)
        with self.assertRaises(ValueError):
            s.kth_smallest_in_range(-1, 5, 1)


class TestRebalance(unittest.TestCase):
    def test_many_inserts_trigger_split(self):
        s = DifferenceCoverSet(4096)
        for x in range(0, 4096, 2):
            s.insert(x)
        self.assertEqual(len(s), 2048)
        # Sanity query over the whole universe.
        self.assertEqual(s.kth_smallest_in_range(0, 4095, 1), 0)
        self.assertEqual(s.kth_smallest_in_range(0, 4095, 2048), 4094)

    def test_insert_delete_then_query(self):
        s = DifferenceCoverSet(1024)
        for x in range(1024):
            s.insert(x)
        for x in range(0, 1024, 2):
            s.delete(x)
        self.assertEqual(len(s), 512)
        # Smallest remaining odd.
        self.assertEqual(s.kth_smallest_in_range(0, 1023, 1), 1)
        self.assertEqual(s.kth_smallest_in_range(0, 1023, 512), 1023)


class TestNoDupes(unittest.TestCase):
    def test_reinsert_same_key_is_idempotent(self):
        s = DifferenceCoverSet(64)
        self.assertTrue(s.insert(3))
        self.assertFalse(s.insert(3))
        self.assertEqual(len(s), 1)


if __name__ == "__main__":
    unittest.main()
