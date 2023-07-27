import json

from mock import patch
from unittest import TestCase

from via.models.journey import Journey
from via.models.journeys import Journeys
from via.models.frame import Frame


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

    @patch("via.settings.MIN_METRES_PER_SECOND", 0)
    @patch("via.settings.GPS_INCLUDE_RATIO", 1)
    def test_edge_quality_map(self):
        self.assertGreater(len(self.test_journeys_single.edge_quality_map), 60)
        self.assertLess(len(self.test_journeys_single.edge_quality_map), 75)
