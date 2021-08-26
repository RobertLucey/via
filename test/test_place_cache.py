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
