import json
import os

from mock import patch
from unittest import TestCase, skipUnless, skip

from via.models.journey import Journey
from via.models.journeys import Journeys
from via.models.frame import Frame


IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class JourneysTest(TestCase):
    @patch("via.settings.MIN_METRES_PER_SECOND", 0)
    @patch("via.settings.GPS_INCLUDE_RATIO", 1)
    def setUp(self):
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

        self.test_journeys_single = Journeys()
        self.test_journeys_single.append(self.test_journey)

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

        self.test_journeys = Journeys()
        self.test_journeys.append(self.test_journey)
        self.test_journeys.append(self.test_journey)

    def test_most_whatever(self):
        self.assertEqual(self.test_journeys.most_northern, 53.3588887)
        self.assertEqual(self.test_journeys.most_southern, 53.332599)
        self.assertEqual(self.test_journeys.most_eastern, -6.2523619)
        self.assertEqual(self.test_journeys.most_western, -6.2661022)

    @skip("Not great from mappymatch")
    @skipUnless(not IS_ACTION, "action_mongo")
    @patch("via.settings.MIN_METRES_PER_SECOND", 0)
    @patch("via.settings.GPS_INCLUDE_RATIO", 1)
    def test_edge_quality_map(self):
        self.assertGreater(len(self.test_journeys_single.edge_quality_map), 60)
        self.assertLess(len(self.test_journeys_single.edge_quality_map), 75)

    def test_content_hash(self):
        journeys = Journeys()

        for i in range(3):
            data = []
            for i in range(1000):
                if i % 5 == 0:
                    data.append(
                        {
                            "time": i,
                            "acc": 1,
                            "gps": {"lat": i / 100000, "lng": i / 100000},
                        }
                    )
                else:
                    data.append(
                        {"time": i, "acc": 1, "gps": {"lat": None, "lng": None}}
                    )

            journey = Journey()
            for dp in data:
                journey.append(dp)

        self.assertEqual(journeys.content_hash, "d751713988987e9331980363e24189ce")

    def test_extend(self):
        journeys = Journeys()

        journey_list = []
        for i in range(3):
            data = []
            for j in range(1000):
                if j % 5 == 0:
                    data.append(
                        {
                            "time": j + i,
                            "acc": 1,
                            "gps": {"lat": j / 100000, "lng": j / 100000},
                        }
                    )
                else:
                    data.append(
                        {"time": j, "acc": 1, "gps": {"lat": None, "lng": None}}
                    )

            journey = Journey()
            for dp in data:
                journey.append(dp)

            journey_list.append(journey)

        journeys.extend(journey_list)

        self.assertEqual(len(journeys), 3)
        self.assertEqual(len(set([j.content_hash for j in journeys])), 3)
