import os
import time
import json
from shutil import copyfile, rmtree

from unittest import TestCase, skip, skipUnless

import geopandas

from via.models.journey import Journey
from via.settings import (
    MONGO_RAW_JOURNEYS_COLLECTION,
    MONGO_NETWORKS_COLLECTION,
    MONGO_PARSED_JOURNEYS_COLLECTION,
)

from via.utils import (
    get_slope,
    should_include_journey,
    window,
    iter_journeys,
    flatten,
    get_journeys,
    angle_between_slopes,
    get_slope,
    filter_edges_from_geodataframe,
    filter_nodes_from_geodataframe,
    get_mongo_interface,
)
from via.models.gps import GPSPoint


IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class UtilTest(TestCase):
    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_journeys(self):
        with open("test/resources/raw_journey_data/1.json") as json_file:
            getattr(get_mongo_interface(), MONGO_RAW_JOURNEYS_COLLECTION).insert_one(
                json.loads(json_file.read())
            )
        self.assertEqual(len(get_journeys()), 1)
        getattr(get_mongo_interface(), MONGO_RAW_JOURNEYS_COLLECTION).drop()
        getattr(get_mongo_interface(), MONGO_NETWORKS_COLLECTION).drop()
        getattr(get_mongo_interface(), MONGO_PARSED_JOURNEYS_COLLECTION).drop()

    def test_window(self):
        self.assertEqual(
            list(window([1, 2, 3, 4, 5])), [(1, 2), (2, 3), (3, 4), (4, 5)]
        )

        self.assertEqual(
            list(window([1, 2, 3, 4, 5], window_size=2)),
            [(1, 2), (2, 3), (3, 4), (4, 5)],
        )

        self.assertEqual(
            list(window([1, 2, 3, 4, 5], window_size=3)),
            [(1, 2, 3), (2, 3, 4), (3, 4, 5)],
        )

    def test_flatten(self):
        self.assertEqual(flatten([[1, 2, 3], [1, 2]]), [1, 2, 3, 1, 2])

    @skip("todo")
    def test_update_edge_data(self):
        pass

    @skip("todo")
    def test_get_edge_angle(self):
        pass

    def test_angle_between_slopes(self):
        self.assertEqual(angle_between_slopes(0, 1), 45)
        self.assertEqual(angle_between_slopes(1, 0), -45)
        self.assertEqual(angle_between_slopes(0, 1, ensure_positive=True), 45)
        self.assertEqual(angle_between_slopes(1, 0, ensure_positive=True), 135)

    def test_get_slope(self):
        self.assertEqual(
            get_slope(
                GPSPoint(0, 0),
                GPSPoint(1, 1),
            ),
            1,
        )

        self.assertEqual(
            get_slope(
                GPSPoint(1, 1),
                GPSPoint(0, 0),
            ),
            1,
        )

    def test_filter_edges_from_geodataframe(self):
        json_dataframe = {
            "osmid": {
                (385708, 446897184, 0): 874491383,
                (385713, 325240800, 0): 22747810,
                (385713, 356046111, 0): 25882052,
                (385713, 325241075, 0): 72248071,
            },
            "oneway": {
                (385708, 446897184, 0): True,
                (385713, 325240800, 0): False,
                (385713, 356046111, 0): False,
                (385713, 325241075, 0): False,
            },
            "lanes": {
                (385708, 446897184, 0): "4",
                (385713, 325240800, 0): "2",
                (385713, 356046111, 0): None,
                (385713, 325241075, 0): "3",
            },
            "ref": {
                (385708, 446897184, 0): "M50",
                (385713, 325240800, 0): None,
                (385713, 356046111, 0): None,
                (385713, 325241075, 0): "L3020",
            },
            "name": {
                (385708, 446897184, 0): "Northern Cross Route Motorway",
                (385713, 325240800, 0): "Mill Road",
                (385713, 356046111, 0): "Church Avenue",
                (385713, 325241075, 0): "Main Street",
            },
        }
        df = geopandas.geodataframe.DataFrame.from_dict(json_dataframe)

        self.assertEqual(
            [
                o["osmid"]
                for o in filter_edges_from_geodataframe(
                    df, [(385708, 446897184, 0), (385713, 325240800, 0)]
                ).to_dict(orient="records")
            ],
            [874491383, 22747810],
        )

    def filter_nodes_from_geodataframe(self):
        json_dataframe = {
            "y": {
                385708: 53.3888025,
                385713: 53.3858427,
                385738: 53.3890498,
                385745: 53.3949888,
            },
            "x": {
                385708: -6.3537148,
                385713: -6.3747161,
                385738: -6.3758631,
                385745: -6.3751901,
            },
            "street_count": {385708: 3, 385713: 4, 385738: 3, 385745: 3},
        }
        df = geopandas.geodataframe.DataFrame.from_dict(json_dataframe)

        self.assertEqual(
            list(
                [
                    o["osmid"]
                    for o in filter_nodes_from_geodataframe(
                        df, [385708, 385713]
                    ).to_dict(orient="records")
                ].index
            ),
            [385708, 385713],
        )
