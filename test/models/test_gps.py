from unittest import TestCase

from via.models.gps import GPSPoint


class GPSPointTest(TestCase):

    def test_parse(self):
        self.assertEqual(
            GPSPoint.parse([1, 2]).serialize(),
            {
                'lat': 1,
                'lng': 2,
                'elevation': None
            }
        )
        self.assertEqual(
            GPSPoint.parse(GPSPoint.parse([1, 2])).serialize(),
            {
                'lat': 1,
                'lng': 2,
                'elevation': None
            }
        )
        self.assertEqual(
            GPSPoint.parse(GPSPoint.parse([1, 2]).serialize()).serialize(),
            {
                'lat': 1,
                'lng': 2,
                'elevation': None
            }
        )
        with self.assertRaises(Exception):
            GPSPoint.parse(None)

    def test_distance_from(self):
        self.assertEqual(
            int(GPSPoint.parse([0, 0]).distance_from(GPSPoint.parse([1, 0]))),
            111195
        )

    def test_eq(self):
        self.assertTrue(GPSPoint.parse([1, 2]) == GPSPoint.parse([1, 2]))
        self.assertFalse(GPSPoint.parse([1, 2]) == GPSPoint.parse([2, 1]))

    def test_point(self):
        self.assertEqual(
            GPSPoint.parse([1, 2]).point,
            (1, 2)
        )

    def test_is_populated(self):
        self.assertTrue(GPSPoint.parse([1, 2]).is_populated)
        self.assertFalse(GPSPoint.parse([None, None]).is_populated)

    def test_serialize(self):
        self.assertEqual(
            GPSPoint.parse([1, 2]).serialize(),
            {
                'lat': 1,
                'lng': 2,
                'elevation': None
            }
        )
