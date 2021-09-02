import os
import time
from shutil import (
    copyfile,
    rmtree
)

from unittest import TestCase, skip

import geopandas

from via.utils import (
    get_slope,
    get_edge_slope,
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
    get_slope,
    filter_edges_from_geodataframe,
    filter_nodes_from_geodataframe
)
from via.constants import (
    REMOTE_DATA_DIR,
    DATA_DIR
)
from via.models.gps import GPSPoint


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

    @skip('todo')
    def test_get_ox_colours(self):
        # TODO: once not doing random quality
        pass

    @skip('todo')
    def test_get_edge_colours(self):
        # TODO: once not doing random quality
        pass

    @skip('todo')
    def test_update_edge_data(self):
        pass

    @skip('todo')
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

    def test_get_slope(self):
        self.assertEqual(
            get_slope(
                GPSPoint(0, 0),
                GPSPoint(1, 1),
            ),
            1
        )

        self.assertEqual(
            get_slope(
                GPSPoint(1, 1),
                GPSPoint(0, 0),
            ),
            1
        )

    def test_get_edge_slope(self):
        self.assertEqual(
            get_edge_slope(
                {1: {'x': 0, 'y': 0}, 2: {'x': 1, 'y': 1}},
                [[[1, 2]]]
            ),
            1
        )

    def test_filter_edges_from_geodataframe(self):
        json_dataframe = {'osmid': {(385708, 446897184, 0): 874491383, (385713, 325240800, 0): 22747810, (385713, 356046111, 0): 25882052, (385713, 325241075, 0): 72248071}, 'oneway': {(385708, 446897184, 0): True, (385713, 325240800, 0): False, (385713, 356046111, 0): False, (385713, 325241075, 0): False}, 'lanes': {(385708, 446897184, 0): '4', (385713, 325240800, 0): '2', (385713, 356046111, 0): None, (385713, 325241075, 0): '3'}, 'ref': {(385708, 446897184, 0): 'M50', (385713, 325240800, 0): None, (385713, 356046111, 0): None, (385713, 325241075, 0): 'L3020'}, 'name': {(385708, 446897184, 0): 'Northern Cross Route Motorway', (385713, 325240800, 0): 'Mill Road', (385713, 356046111, 0): 'Church Avenue', (385713, 325241075, 0): 'Main Street'}}
        df = geopandas.geodataframe.DataFrame.from_dict(json_dataframe)

        self.assertEqual(
            [o['osmid'] for o in filter_edges_from_geodataframe(df, [(385708, 446897184, 0), (385713, 325240800, 0)]).to_dict(orient='records')],
            [874491383, 22747810]
        )

    def filter_nodes_from_geodataframe(self):
        json_dataframe = {'y': {385708: 53.3888025, 385713: 53.3858427, 385738: 53.3890498, 385745: 53.3949888}, 'x': {385708: -6.3537148, 385713: -6.3747161, 385738: -6.3758631, 385745: -6.3751901}, 'street_count': {385708: 3, 385713: 4, 385738: 3, 385745: 3}}
        df = geopandas.geodataframe.DataFrame.from_dict(json_dataframe)

        self.assertEqual(
            list([o['osmid'] for o in filter_nodes_from_geodataframe(df, [385708, 385713]).to_dict(orient='records')].index),
            [385708, 385713]
        )
