import json

from unittest import TestCase, skip

from via.models.journey import Journey
from via.models.frame import Frame

from via.edge_cache import get_edge_data


class EdgeCacheTest(TestCase):

    def setUp(self):

        with open('test/resources/just_route.json') as json_file:
            self.test_data = json.load(json_file)

        self.test_journey = Journey()
        for d in self.test_data:
            self.test_journey.append(
                Frame(
                    d['time'],
                    {'lat': d['lat'], 'lng': d['lng']},
                    1  # acceleration, don't really care at the mo
                )
            )

    def test_get(self):
        self.assertEqual(
            get_edge_data(389281, 135109553, graph=self.test_journey.graph),
            {0: {'osmid': 14039949, 'oneway': True, 'name': 'York Street', 'highway': 'unclassified', 'maxspeed': '30', 'length': 34.217}}
        )

    @skip('todo')
    def test_caching(self):
        # Make sure it just does get_edge_data once
        pass
