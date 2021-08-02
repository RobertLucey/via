import json
from mock import patch

from unittest import TestCase

from bike.utils import flatten
from bike.models.frame import Frame
from bike.models.journey import Journey
from bike.models.partial import (
    Partial,
    partials_from_journey
)


class PartialTest(TestCase):

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

    @patch('bike.models.partial.PARTIAL_SPLIT_INTO', 2)
    def test_partials_from_journey(self):
        partials = partials_from_journey(self.test_journey)
        self.assertIsInstance(partials, list)
        self.assertEqual(len(partials), 2)

        self.assertEqual(
            len(flatten([p._data for p in partials])),
            len(self.test_journey._data)
        )

    def test_serialize(self):
        partials = partials_from_journey(self.test_journey)
        data = partials[0].serialize()

        del data['data']
        del data['uuid']

        self.assertEqual(
            data,
            {
                'is_partial': True,
                'suspension': True,
                'transport_type': 'mountain',
            }
        )

    def test_save(self):
        pass

    def test_from_file(self):
        pass

    def test_parse(self):
        pass
