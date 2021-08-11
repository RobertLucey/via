import json
import os

from mock import patch

from unittest import TestCase

from bike.utils import flatten
from bike.models.frame import Frame
from bike.models.journey import Journey
from bike.models.partial import (
    Partial,
    partials_from_journey
)
from bike.constants import PARTIAL_DATA_DIR


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
                    1  # acceleration, don't really care at the mo
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

    @patch('bike.models.partial.PARTIAL_RANDOMIZE_DATA_ORDER', False)
    def test_parse(self):
        partials = partials_from_journey(self.test_journey)
        data = partials[0]
        self.assertEqual(
            Partial.parse(data).serialize(),
            data.serialize()
        )

        self.assertEqual(
            Partial.parse(data.serialize()).serialize(),
            data.serialize()
        )

        with self.assertRaises(NotImplementedError):
            Partial.parse(None)

    def test_save(self):
        partials = partials_from_journey(self.test_journey)
        partial = partials[0]
        filepath = os.path.join(PARTIAL_DATA_DIR, str(partial.uuid) + '.json')

        self.assertFalse(os.path.exists(filepath))

        partial.save()

        self.assertTrue(os.path.exists(filepath))

    @patch('bike.models.partial.PARTIAL_RANDOMIZE_DATA_ORDER', False)
    def test_from_file(self):
        partials = partials_from_journey(self.test_journey)
        partial = partials[0]
        filepath = os.path.join(PARTIAL_DATA_DIR, str(partial.uuid) + '.json')

        partial.save()

        from_file_partial = Partial.from_file(filepath)

        # json thing cause acc can be () or [] FIXME
        self.assertEqual(
            json.loads(json.dumps(partial.serialize())),
            json.loads(json.dumps(from_file_partial.serialize()))
        )
