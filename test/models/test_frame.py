from unittest import TestCase

from bike.models.frame import (
    Frame,
    Frames
)


class FrameTest(TestCase):

    def test_completeness(self):
        self.assertTrue(Frame(0.0, {'lat': 0.0, 'lng': 1.0}, (1.0, 1.0, 1.0)).is_complete)
        self.assertFalse(Frame(0.0, {'lat': 0.0, 'lng': 1.0}, (1.0, 1.0)).is_complete)
        self.assertFalse(Frame(0.0, {'lat': 0.0, 'lng': None}, (1.0, 1.0, 1.0)).is_complete)

    def test_lat(self):
        self.assertEqual(
            Frame(
                0.0,
                {'lat': 0.0, 'lng': 1.0},
                (1.0, 2.0, 3.0)
            ).gps.lat,
            0
        )

    def test_lng(self):
        self.assertEqual(
            Frame(
                0.0,
                {'lat': 0.0, 'lng': 1.0},
                (1.0, 1.0, 1.0)
            ).gps.lng,
            1
        )

    def test_distance_from_point(self):
        pass

    def test_serialize(self):
        self.assertEqual(
            Frame(0.0, {'lat': 0.0, 'lng': 1.0}, (1.0, 2.0, 3.0)).serialize(),
            {
                'time': 0.0,
                'gps': {'lat': 0.0, 'lng': 1.0, 'elevation': None},
                'acc': (1.0, 2.0, 3.0)
            }
        )
