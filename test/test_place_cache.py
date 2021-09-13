from unittest import TestCase

from via.place_cache import PlaceCache


class PlaceCacheTest(TestCase):

    def test_get(self):
        cache = PlaceCache()
        self.assertFalse('cork ireland' in cache.data)
        london = cache.get('Cork, Ireland')
        self.assertEqual(
            london,
            {
                'east': -8.3567461,
                'north': 51.9623212,
                'south': 51.8275379,
                'west': -8.6368609
            }
        )
        self.assertTrue('cork ireland' in cache.data)

    def test_get_by_bbox_within(self):
        cache = PlaceCache()
        self.assertIsNotNone(
            cache.get_by_bbox(
                {
                    'north': 53.61,
                    'south': 53.4,
                    'east': -6.2,
                    'west': -6.3,
                }
            )
        )

    def test_get_by_bbox_exact(self):
        cache = PlaceCache()
        self.assertIsNotNone(
            cache.get_by_bbox(
                {
                    'north': 53.626487,
                    'south': 53.3018049,
                    'east': -6.1366563,
                    'west': -6.433500
                }
            )
        )

    def test_get_by_bbox_nowhere(self):
        cache = PlaceCache()
        self.assertIsNone(
            cache.get_by_bbox(
                {
                    'north': 0,
                    'south': 0,
                    'east': 0,
                    'west': 0,
                }
            )
        )
