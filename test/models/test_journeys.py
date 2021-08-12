import json
import hashlib
import uuid
import os

from unittest import TestCase

from bike.models.journey import Journey
from bike.models.journeys import Journeys
from bike.models.frame import Frame


class JourneysTest(TestCase):

    def setUp(self):
        with open('test/resources/dublin_route.json') as json_file:
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

        with open('test/resources/dublin_route.json') as json_file:
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
            ['None_None']  # FIXME
        )
        self.assertEqual(
            len(journeys['None_None']._data),  # FIXME
            (len(self.test_journey._data) * 2)
        )

    def test_edge_quality_map(self):
        self.assertEqual(
            len(self.test_journeys_single.edge_quality_map),
            77
        )

    def test_plot_routes_too_few(self):
        with self.assertRaises(Exception):
            Journeys().plot_routes()

        self.test_journeys._data = [self.test_journeys._data[0]]

        with self.assertRaises(Exception):
            self.test_journeys.plot_routes()

    def test_plot_routes_nothing_fancy(self):
        img_uuid = str(uuid.uuid4())
        fp = os.path.join('/tmp/', img_uuid) + '.jpg'
        self.test_journeys.plot_routes(
            plot_kwargs={
                'show': False,
                'save': True,
                'filepath': os.path.join('/tmp/', img_uuid) + '.jpg'
            }
        )

        self.assertEqual(
            hashlib.md5(open(fp, 'rb').read()).hexdigest(),
            'cf5f2b5fcdb64e2f264c3ad566ef134b'
        )

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
