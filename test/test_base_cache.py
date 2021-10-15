from unittest import TestCase
from mock import patch

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

    @patch('via.settings.VERSION', '0.0.1')
    def test_dir(self):
        from via import settings
        self.assertEqual(
            BaseCache(cache_type='blahblah').dir,
            f'/tmp/via/cache/blahblah/{settings.VERSION}'
        )

    @patch('via.settings.VERSION', '0.0.1')
    def test_fp(self):
        from via import settings
        self.assertEqual(
            BaseCache(cache_type='blahblah').fp,
            f'/tmp/via/cache/blahblah/{settings.VERSION}/cache.pickle'
        )
