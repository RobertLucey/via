import json
import hashlib
import uuid
import os

from mock import patch
from unittest import TestCase, skip
from PIL import Image
import imagehash

from via.models.journey import Journey
from via.models.journeys import Journeys
from via.models.frame import Frame


class JourneysTest(TestCase):

    @patch('via.settings.MIN_METRES_PER_SECOND', 0)
    @patch('via.settings.GPS_INCLUDE_RATIO', 1)
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

        self.test_journeys_single = Journeys()
        self.test_journeys_single.append(self.test_journey)

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

        self.test_journeys = Journeys()
        self.test_journeys.append(self.test_journey)
        self.test_journeys.append(self.test_journey)

    def test_most_whatever(self):
        self.assertEqual(
            self.test_journeys.most_northern,
            53.3588887
        )
        self.assertEqual(
            self.test_journeys.most_southern,
            53.332599
        )
        self.assertEqual(
            self.test_journeys.most_eastern,
            -6.2523619
        )
        self.assertEqual(
            self.test_journeys.most_western,
            -6.2661022
        )

    def test_get_mega_journeys(self):
        journeys = self.test_journeys.get_mega_journeys()
        self.assertEqual(
            list(journeys.keys()),
            ['unknown_None']  # FIXME
        )
        self.assertEqual(
            len(journeys['unknown_None']._data),  # FIXME
            (len(self.test_journey._data) * 2)
        )

    @patch('via.settings.MIN_METRES_PER_SECOND', 0)
    @patch('via.settings.GPS_INCLUDE_RATIO', 1)
    def test_edge_quality_map(self):
        self.assertEqual(
            len(self.test_journeys_single.edge_quality_map),
            63
        )

    def test_plot_routes_too_few(self):
        with self.assertRaises(Exception):
            Journeys().plot_routes()

    def test_plot_routes_nothing_fancy(self):
        img_uuid = str(uuid.uuid4())
        fp = os.path.join('/tmp/', img_uuid) + '.jpg'
        self.test_journeys.plot_routes(
            use_graph_cache=False,
            plot_kwargs={
                'show': False,
                'save': True,
                'filepath': os.path.join('/tmp/', img_uuid) + '.jpg'
            }
        )

        hash_generated = imagehash.average_hash(Image.open(fp))
        hash_resource = imagehash.average_hash(Image.open('test/resources/images/route_1.jpg'))

        self.assertEqual(hash_generated, hash_resource)

    @skip('not implemented')
    def test_plot_routes_use_closest(self):
        img_uuid = str(uuid.uuid4())
        fp = os.path.join('/tmp/', img_uuid) + '.jpg'
        self.test_journeys.plot_routes(
            use_closest_edge_from_base=True,
            plot_kwargs={
                'show': False,
                'save': True,
                'filepath': os.path.join('/tmp/', img_uuid) + '.jpg'
            }
        )

        self.assertEqual(
            hashlib.md5(open(fp, 'rb').read()).hexdigest(),
            'd79a8a56de0c050d9f57bebee8589274'
        )
