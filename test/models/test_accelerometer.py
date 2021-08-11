from unittest import TestCase

from bike.models.accelerometer import AccelerometerPoint


class AccelerometerPointTest(TestCase):


    def test_serialize(self):
        self.assertEqual(
            AccelerometerPoint(1, None, 3).serialize(),
            None
        )

    def test_parse(self):
        self.assertEqual(
            AccelerometerPoint.parse(
                (
                    1,
                    2,
                    3
                )
            ).serialize(),
            {
                'x': 1,
                'y': 2,
                'z': 3
            }
        )

        self.assertEqual(
            AccelerometerPoint.parse(
                {
                    'x': 1,
                    'y': 2,
                    'z': 3
                }
            ).serialize(),
            {
                'x': 1,
                'y': 2,
                'z': 3
            }
        )

    def test_is_populated(self):
        self.assertTrue(AccelerometerPoint(1, 2, 3).is_populated)
        self.assertFalse(AccelerometerPoint(1, None, 3).is_populated)
