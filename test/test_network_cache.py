import os
import json
from shutil import copyfile, rmtree

from unittest import TestCase, skip

from via.network_cache import SingleNetworkCache, GroupedNetworkCaches, NetworkCache


class SingleNetworkCacheTest(TestCase):
    def test_since_last_accessed(self):
        network_cache = SingleNetworkCache("something")
        self.assertLess(network_cache.since_last_accessed, 0.0001)

    def test_dir(self):
        network_cache = SingleNetworkCache("something")
        self.assertEqual(
            [
                i
                for i in network_cache.dir.split("/")[:5]
                + [network_cache.dir.split("/")[-1]]
                if i
            ],
            ["tmp", "via", "cache", "network_cache", "something"],
        )

    def test_get_by_id(self):
        network_cache = SingleNetworkCache("something")
        network_cache.networks = {
            "a": 1,
            "b": 2,
            "c": 3,
        }
        network_cache.data = {
            "a": {"a1": 1, "a2": 2},
            "b": {"b1": 1, "b2": 2},
            "c": {"c1": 1, "c2": 2},
        }
        self.assertEqual(network_cache.get_by_id("a"), {"a1": 1, "a2": 2, "network": 1})


class GroupedNetworkCacheTest(TestCase):
    def test_get_by_id(self):
        cache = GroupedNetworkCaches(cache_type="blah")

        single_network_cache = SingleNetworkCache("something")
        single_network_cache.networks = {
            "a": 1,
            "b": 2,
            "c": 3,
        }
        single_network_cache.data = {
            "a": {"a1": 1, "a2": 2},
            "b": {"b1": 1, "b2": 2},
            "c": {"c1": 1, "c2": 2},
        }

        cache.loaded = True
        cache.data = {
            "a": single_network_cache,
            "b": single_network_cache,
            "c": single_network_cache,
        }
        self.assertEqual(cache.get_by_id("b"), {"b1": 1, "b2": 2, "network": 2})


class NetworkCacheTest(TestCase):
    def test_something(self):
        cache = NetworkCache()
        cache.network_caches = {
            "a": 1,  # Val should be GroupedNetworkCache
            "b": 2,
            "c": 3,
        }
        # cache.get_by_id("b")
