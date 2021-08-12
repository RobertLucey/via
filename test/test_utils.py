from unittest import TestCase

import time

from bike.utils import (
    get_ox_colours,
    is_journey_data_file,
    get_data_files,
    window,
    iter_journeys,
    sleep_until,
    get_idx_default,
    force_list,
    flatten,
    get_journeys
)


@sleep_until(0.5)
def sleep_a_bit():
    return None


class UtilTest(TestCase):

    def test_window(self):
        self.assertEqual(
            list(window([1, 2, 3, 4, 5])),
            [(1, 2), (2, 3), (3, 4), (4, 5)]
        )

        self.assertEqual(
            list(window([1, 2, 3, 4, 5], window_size=2)),
            [(1, 2), (2, 3), (3, 4), (4, 5)]
        )

        self.assertEqual(
            list(window([1, 2, 3, 4, 5], window_size=3)),
            [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        )

    def test_sleep_until(self):
        st = time.monotonic()
        sleep_a_bit()
        et = time.monotonic()
        taken = et - st

        self.assertTrue(taken >= 0.5)

    def test_get_idx_default(self):
        self.assertEqual(
            get_idx_default([1, 2, 3], 0, None),
            1
        )
        self.assertEqual(
            get_idx_default([1, 2, 3], 9, None),
            None
        )

    def test_force_list(self):
        self.assertEqual(
            force_list([]),
            []
        )
        self.assertEqual(
            force_list([[]]),
            [[]]
        )
        self.assertEqual(
            force_list(1),
            [1]
        )

    def test_flatten(self):
        self.assertEqual(
            flatten([[1, 2, 3], [1, 2]]),
            [1, 2, 3, 1, 2]
        )

    def test_get_ox_colours(self):
        # TODO: once not doing random quality
        pass

    def test_get_edge_colours(self):
        # TODO: once not doing random quality
        pass
