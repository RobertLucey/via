from unittest import TestCase

from via.models.point import (
    FramePoint,
    FramePoints
)


class FramePointTest(TestCase):

    def test_parse(self):
        self.assertEqual(
            FramePoint.parse(
                {
                    'time': 10,
                    'gps': {'lat': 1, 'lng': 2},
                    'acc': [1, 2, 3, 4]
                }
            ).serialize(),
            {
                'acc': [1, 2, 3, 4],
                'context': {'post': [], 'pre': []},
                'gps': {'elevation': None, 'lat': 1, 'lng': 2},
                'time': 10
            }
        )

        self.assertEqual(
            FramePoint.parse(
                FramePoint.parse(
                    {
                        'time': 10,
                        'gps': {'lat': 1, 'lng': 2},
                        'acc': [1, 2, 3, 4]
                    }
                )
            ).serialize(),
            {
                'acc': [1, 2, 3, 4],
                'context': {'post': [], 'pre': []},
                'gps': {'elevation': None, 'lat': 1, 'lng': 2},
                'time': 10
            }
        )


class FramePointsTest(TestCase):

    def test_get_multi_point(self):
        points = FramePoints()
        points.append(FramePoint.parse({'time': 10, 'gps': {'lat': 1, 'lng': 2}, 'acc': [1, 2, 3, 4]}))
        points.append(FramePoint.parse({'time': 20, 'gps': {'lat': 3, 'lng': 4}, 'acc': [1, 2, 3, 4]}))
        points.append(FramePoint.parse({'time': 30, 'gps': {'lat': 5, 'lng': 6}, 'acc': [1, 2, 3, 4]}))

        multi_points = points.get_multi_points()
        self.assertEqual(multi_points.centroid.x, 5)
        self.assertEqual(multi_points.centroid.y, 4)

    def test_is_in_place(self):
        points = FramePoints()
        points.append(FramePoint.parse({'time': 10, 'gps': {'lat': 53.3497913, 'lng': -6.2603686}, 'acc': [1, 2, 3, 4]}))

        self.assertTrue(points.is_in_place('Dublin, Ireland'))
        self.assertFalse(points.is_in_place('Paris, France'))
        self.assertFalse(points.is_in_place('Blah blah blah'))

    def test_country(self):
        points = FramePoints()
        points.append(FramePoint.parse({'time': 10, 'gps': {'lat': 53.3497913, 'lng': -6.2603686}, 'acc': [1, 2, 3, 4]}))
        self.assertEqual(points.country, 'IE')

    def test_content_hash(self):
        points = FramePoints()
        points.append(FramePoint.parse({'time': 10, 'gps': {'lat': 1, 'lng': 2}, 'acc': [1, 2, 3, 4]}))
        points.append(FramePoint.parse({'time': 20, 'gps': {'lat': 3, 'lng': 4}, 'acc': [1, 2, 3, 4]}))
        points.append(FramePoint.parse({'time': 30, 'gps': {'lat': 5, 'lng': 6}, 'acc': [1, 2, 3, 4]}))
        self.assertEqual(
            points.content_hash,
            'c8765c4a19d013541f9c2d2c9428c178'
        )
