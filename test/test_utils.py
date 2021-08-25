import os
from shutil import copyfile, rmtree

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
    get_journeys,
    angle_between_slopes,
    get_angle
)
from bike.constants import (
    REMOTE_DATA_DIR,
    DATA_DIR
)
from bike.models.gps import GPSPoint


@sleep_until(0.5)
def sleep_a_bit():
    return None


class UtilTest(TestCase):

    def setUp(self):
        try:
            rmtree(DATA_DIR)
        except Exception as ex:
            pass
        os.makedirs(REMOTE_DATA_DIR, exist_ok=True)
        copyfile(
            'test/resources/journey_point_at_node.json',
            os.path.join(REMOTE_DATA_DIR, 'journey_point_at_node.json')
        )
        copyfile(
            'test/resources/just_route.json',
            os.path.join(REMOTE_DATA_DIR, 'just_route.json')
        )

    def test_is_journey_data_file(self):
        self.assertTrue(
            is_journey_data_file(
                os.path.join(
                    REMOTE_DATA_DIR,
                    'journey_point_at_node.json'
                )
            )
        )

        self.assertFalse(
            is_journey_data_file(
                os.path.join(
                    REMOTE_DATA_DIR,
                    'just_route.json'
                )
            )
        )

        self.assertFalse(
            is_journey_data_file(
                '/dev/null'
            )
        )

    def test_get_journeys(self):
        self.assertEqual(
            len(get_journeys()),
            1
        )


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

    def test_update_edge_data(self):
        pass

    def test_get_angle(self):
        self.assertEqual(
            get_angle(
                GPSPoint(0, 0),
                GPSPoint(1, 1),
            ),
            1
        )

        self.assertEqual(
            get_angle(
                GPSPoint(1, 1),
                GPSPoint(0, 0),
            ),
            1
        )

    def test_get_edge_angle(self):
        pass

    def test_angle_between_slopes(self):
        self.assertEqual(
            angle_between_slopes(0, 1),
            45
        )
        self.assertEqual(
            angle_between_slopes(1, 0),
            -45
        )
        self.assertEqual(
            angle_between_slopes(0, 1, ensure_positive=True),
            45
        )
        self.assertEqual(
            angle_between_slopes(1, 0, ensure_positive=True),
            135
        )
