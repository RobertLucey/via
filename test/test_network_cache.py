import os
import json
from shutil import copyfile, rmtree

from unittest import TestCase, skip, skipUnless

from networkx.classes.multidigraph import MultiDiGraph

from via.utils import get_graph_id
from via.models.journey import Journey
from via.network_cache import NetworkCache

from .utils import wipe_mongo

IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class NetworkCacheTest(TestCase):
    def setUp(self):
        wipe_mongo()

    def tearDown(self):
        wipe_mongo()

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_none(self):
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

        cache = NetworkCache()
        self.assertIsNone(cache.get(journey))

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_set(self):
        graph = MultiDiGraph()
        graph_id = get_graph_id(graph)

        cache = NetworkCache()
        self.assertIsNone(cache.get_from_mongo(graph_id))
        cache.set(graph, {"north": 0, "south": 0, "east": 0, "west": 0})
        self.assertIsNotNone(cache.get_from_mongo(graph_id))
