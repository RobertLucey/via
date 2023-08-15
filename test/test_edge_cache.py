import json
import os

from unittest import TestCase, skip, skipUnless

from via.models.journey import Journey
from via.models.frame import Frame
from via.utils import get_mongo_interface

from via.edge_cache import get_edge_data

from .utils import wipe_mongo


IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class EdgeCacheTest(TestCase):
    def tearDown(self):
        wipe_mongo()

    def setUp(self):
        wipe_mongo()

        with open("test/resources/just_route.json") as json_file:
            self.test_data = json.load(json_file)

        self.test_journey = Journey()
        for d in self.test_data:
            self.test_journey.append(
                Frame(
                    d["time"],
                    {"lat": d["lat"], "lng": d["lng"]},
                    1,  # acceleration, don't really care at the mo
                )
            )

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get(self):
        self.assertEqual(
            get_edge_data(389281, 135109553, graph=self.test_journey.graph)[0]["osmid"],
            14039949,
        )
        self.assertEqual(
            get_edge_data(389281, 135109553, graph=self.test_journey.graph)[0]["name"],
            "York Street",
        )

    def test_get_no_graph(self):
        self.assertEqual(get_edge_data(1, 2, graph=None), None)
