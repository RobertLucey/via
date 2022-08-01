import os

from unittest import TestCase
from mock import patch

from via.settings import VERSION
from via.base_cache import BaseCache


class BaseCacheTest(TestCase):
    def test_init(self):
        self.assertFalse(BaseCache(cache_type="blahblah").loaded)
        self.assertEqual(BaseCache(cache_type="blahblah").data, {})
        self.assertEqual(BaseCache(cache_type="blahblah").cache_type, "blahblah")

    def test_get(self):
        cache = BaseCache(cache_type="test_get")
        cache.set("one", 1)
        self.assertEqual(cache.get("one"), 1)

    def test_delete(self):
        cache = BaseCache(cache_type="test_delete")
        cache.set("one", 1, skip_save=True)
        cache.set("two", 2, skip_save=True)
        cache.save()

        self.assertTrue(os.path.exists(cache.fp))

        cache.delete()

        self.assertFalse(os.path.exists(cache.fp))

    def test_save(self):
        cache = BaseCache(cache_type="test_save")
        cache.delete()
        cache.set("one", 1, skip_save=True)
        cache.set("two", 2, skip_save=True)
        cache.save()

        cache = BaseCache(cache_type="test_save")
        self.assertEqual(cache.get("one"), 1)

    def test_load_content(self):
        cache = BaseCache(cache_type="test_load_content")
        cache.set("one", 1)
        cache.save()

        cache = BaseCache(cache_type="test_load_content")
        cache.load()
        self.assertEqual(cache.data["one"], 1)

    def test_load_empty(self):
        cache = BaseCache(cache_type="blahblah")
        cache.load()
        self.assertTrue(cache.loaded)
        self.assertEqual(cache.data, {})

    def test_create_dirs(self):
        cache = BaseCache(cache_type="testcreatedirs")
        cache.create_dirs()
        self.assertTrue(os.path.exists(os.path.dirname(cache.fp)))

    @patch("via.settings.VERSION", "0.0.1")
    def test_dir(self):
        from via import settings

        self.assertEqual(
            BaseCache(cache_type="blahblah").dir,
            f"/tmp/via/cache/blahblah/{settings.VERSION}",
        )

    @patch("via.settings.VERSION", "0.0.1")
    def test_fp(self):
        from via import settings

        self.assertEqual(
            BaseCache(cache_type="blahblah", fn="cache.pickle").fp,
            f"/tmp/via/cache/blahblah/{settings.VERSION}/cache.pickle",
        )
