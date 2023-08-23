import os
import operator
import time
import json
import datetime
import pickle
from packaging import version
from shutil import copyfile, rmtree

from unittest import TestCase, skip, skipUnless

from networkx.classes.multidigraph import MultiDiGraph

import geopandas

from via.models.journey import Journey
from via.settings import MONGO_RAW_JOURNEYS_COLLECTION

from via.utils import (
    should_include_journey,
    window,
    iter_journeys,
    get_journeys,
    filter_edges_from_geodataframe,
    filter_nodes_from_geodataframe,
    get_graph_id,
    get_combined_id,
    update_edge_data,
)
from via.models.gps import GPSPoint
from via.db import db

from .utils import wipe_mongo


IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class UtilTest(TestCase):
    def setUp(self):
        wipe_mongo()

    def tearDown(self):
        wipe_mongo()

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_journeys(self):
        with open("test/resources/raw_journey_data/1.json") as json_file:
            db.raw_journeys.insert_one(json.loads(json_file.read()))
        self.assertEqual(len(get_journeys()), 1)

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

    def test_should_include_journey(self):
        data = []
        for i in range(1000):
            if i % 5 == 0:
                data.append(
                    {"time": i, "acc": 1, "gps": {"lat": i / 100000, "lng": i / 100000}}
                )
            else:
                data.append({"time": i, "acc": 1, "gps": {"lat": None, "lng": None}})

        journey = Journey()
        for dp in data:
            journey.append(dp)

        # control
        self.assertTrue(should_include_journey(journey))

        # version
        journey._version = "1000.1.1"
        self.assertFalse(
            should_include_journey(
                journey, version_op=operator.gt, version=version.parse("2.2.2")
            )
        )

        # version_op
        journey._version = "1.1.1"
        self.assertFalse(
            should_include_journey(
                journey, version_op=operator.gt, version=version.parse("2.2.2")
            )
        )

        # place
        self.assertFalse(should_include_journey(journey, place="Paris, France"))

        # earliest_time
        journey._timestamp = "2023-01-01 00:00:00"
        self.assertFalse(
            should_include_journey(journey, earliest_time=datetime.datetime(2024, 1, 1))
        )

        # latest_time
        self.assertFalse(
            should_include_journey(journey, latest_time=datetime.datetime(2022, 1, 1))
        )

        # area
        data = []
        for i in range(1000):
            if i % 5 == 0:
                data.append(
                    {"time": i, "acc": 1, "gps": {"lat": i / 1000, "lng": i / 1000}}
                )
            else:
                data.append({"time": i, "acc": 1, "gps": {"lat": None, "lng": None}})

        journey = Journey()
        for dp in data:
            journey.append(dp)

        self.assertFalse(should_include_journey(journey))

        # enough data
        data = []
        for i in range(100):
            if i % 5 == 0:
                data.append(
                    {"time": i, "acc": 1, "gps": {"lat": i / 100000, "lng": i / 100000}}
                )
            else:
                data.append({"time": i, "acc": 1, "gps": {"lat": None, "lng": None}})

        journey = Journey()
        for dp in data:
            journey.append(dp)

        self.assertFalse(should_include_journey(journey))

    def test_get_graph_id(self):
        self.assertEqual(
            get_graph_id(MultiDiGraph()), "bcd8b0c2eb1fce714eab6cef0d771acc"
        )

        unreliable_id = get_graph_id(MultiDiGraph(), True)
        self.assertEqual(unreliable_id, get_graph_id(MultiDiGraph(), True))

    def test_update_edge_data(self):
        cork = None
        with open("test/resources/cork_graph.pickle", "rb") as f:
            cork = pickle.load(f)

        # for start, end, _ in cork.edges:
        #    print(get_combined_id(start, end))

        edge_data_map = {
            "combined_edge_id": {"some": "data"},
            16262647295: {"custom1": 1},
            16262647192: {"custom1": 2},
        }

        update_edge_data(cork, edge_data_map)

        vals = []
        for start, end, _ in cork.edges:
            if set(edge_data_map.keys()).intersection(
                set([get_combined_id(start, end)])
            ):
                self.assertTrue("custom1" in cork.get_edge_data(start, end)[0])
                vals.append(cork.get_edge_data(start, end)[0]["custom1"])
            else:
                self.assertFalse("custom1" in cork.get_edge_data(start, end)[0])
                self.assertFalse("custom1" in cork.get_edge_data(start, end)[0])
                self.assertFalse("custom1" in cork.get_edge_data(start, end)[0])

        self.assertEqual(sorted(vals), [1, 1, 2, 2])
