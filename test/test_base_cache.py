from unittest import TestCase

from via.base_cache import BaseCache


class BaseCacheTest(TestCase):

    def test_init(self):
        self.assertFalse(
            BaseCache(cache_type='blahblah').loaded
        )
        self.assertEqual(
            BaseCache(cache_type='blahblah').data,
            {}
        )
        self.assertEqual(
            BaseCache(cache_type='blahblah').cache_type,
            'blahblah'
        )

    def test_get(self):
        cache = BaseCache(cache_type='test_get')
        cache.set('one', 1)
        self.assertEqual(
            cache.get('one'),
            1
        )

    def test_save(self):
        cache = BaseCache(cache_type='test_get')
        cache.set('one', 1)
        cache.save()

        cache = BaseCache(cache_type='test_get')
        self.assertEqual(
            cache.get('one'),
            1
        )

    def test_load_content(self):
        cache = BaseCache(cache_type='test_get')
        cache.set('one', 1)
        cache.save()

        cache = BaseCache(cache_type='test_get')
        cache.load()
        self.assertEqual(
            cache.data,
            {
                'one': 1
            }
        )

    def test_load_empty(self):
        cache = BaseCache(cache_type='blahblah')
        cache.load()
        self.assertTrue(cache.loaded)
        self.assertEqual(cache.data, {})

    def test_dir(self):
        self.assertEqual(
            BaseCache(cache_type='blahblah').dir,
            '/tmp/via/cache/blahblah/0.0.1'
        )

    def test_fp(self):
        self.assertEqual(
            BaseCache(cache_type='blahblah').fp,
            '/tmp/via/cache/blahblah/0.0.1/cache.pickle'
        )
