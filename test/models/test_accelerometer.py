from unittest import TestCase

from bike.models.accelerometer import AccelerometerPoint


class AccelerometerPointTest(TestCase):

    def test_serialize(self):
        self.assertEqual(
            AccelerometerPoint(1).serialize(),
            1
        )
        self.assertEqual(
            AccelerometerPoint([1, 2]).serialize(),
            [1, 2]
        )
        self.assertEqual(
            AccelerometerPoint([1, 2]).serialize(),
            [1, 2]
        )

    def test_is_populated(self):
        self.assertTrue(AccelerometerPoint(1, 2, 3).is_populated)
        self.assertFalse(AccelerometerPoint(None).is_populated)
