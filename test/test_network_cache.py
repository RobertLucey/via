import os
import json
import re
from shutil import copyfile, rmtree

from unittest import TestCase, skip

from gridfs import GridFS
from networkx.classes.multidigraph import MultiDiGraph

from via.settings import MONGO_NETWORKS_COLLECTION
from via.utils import get_graph_id, get_mongo_interface
from via.models.journey import Journey
from via.network_cache import NetworkCache


class NetworkCacheTest(TestCase):
    def setUp(self):
        mongo_interface = get_mongo_interface()
        getattr(mongo_interface, MONGO_NETWORKS_COLLECTION).drop()
        grid = GridFS(mongo_interface)
        for i in grid.find({"filename": {"$regex": f'^{re.escape("test_")}'}}):
            grid.delete(i._id)

    def tearDown(self):
        mongo_interface = get_mongo_interface()
        getattr(mongo_interface, MONGO_NETWORKS_COLLECTION).drop()
        grid = GridFS(mongo_interface)
        for i in grid.find({"filename": {"$regex": f'^{re.escape("test_")}'}}):
            grid.delete(i._id)

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

    def test_set(self):
        graph = MultiDiGraph()
        graph_id = get_graph_id(graph)

        cache = NetworkCache()
        self.assertIsNone(cache.get_from_mongo(graph_id))
        cache.set(graph, {"north": 0, "south": 0, "east": 0, "west": 0})
        self.assertIsNotNone(cache.get_from_mongo(graph_id))
