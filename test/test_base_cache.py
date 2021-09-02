from unittest import TestCase, skip

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

    @skip('todo')
    def test_get(self):
        pass

    @skip('todo')
    def test_set(self):
        pass

    @skip('todo')
    def test_save(self):
        pass

    @skip('todo')
    def test_load_content(self):
        pass

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
