import json

import mock

from unittest import TestCase

from bike.models.journey import Journey
from bike.models.frame import Frame

from bike.edge_cache import get_edge_data


class EdgeCacheTest(TestCase):

    def setUp(self):

        with open('test/resources/dublin_route.json') as json_file:
            self.test_data = json.load(json_file)

        self.test_journey = Journey()
        for d in self.test_data:
            self.test_journey.append(
                Frame(
                    d['time'],
                    {'lat': d['lat'], 'lng': d['lng']},
                    ()  # acceleration, don't really care at the mo
                )
            )

    def test_get(self):
        self.assertEqual(
            get_edge_data(self.test_journey.graph, 389281, 135109553),
            {0: {'osmid': 14039949, 'oneway': True, 'name': 'York Street', 'highway': 'unclassified', 'maxspeed': '30', 'length': 34.217}}
        )

    def test_caching(self):
        # Make sure it just does get_edge_data once
        pass
