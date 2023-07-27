import os
import json
from shutil import copyfile, rmtree

from unittest import TestCase, skip

from via.network_cache import NetworkCache


class NetworkCacheTest(TestCase):
    def test_something(self):
        cache = NetworkCache()
        cache.network_caches = {
            "a": 1,  # Val should be GroupedNetworkCache
            "b": 2,
            "c": 3,
        }
        # cache.get_by_id("b")
