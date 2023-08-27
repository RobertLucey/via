import datetime
import pickle

from unittest import TestCase, skip, skipUnless

from via.geojson.utils import geojson_from_graph

from ..utils import wipe_mongo


class GeoJsonUtilTest(TestCase):
    def setUp(self):
        wipe_mongo()

    def tearDown(self):
        wipe_mongo()

    def test_geojson_from_graph(self):
        cork = None
        with open("test/resources/cork_graph.pickle", "rb") as f:
            cork = pickle.load(f)

        geo = geojson_from_graph(cork)

        self.assertEqual(geo["type"], "FeatureCollection")
        self.assertGreater(len(geo["features"]), 41036)
        self.assertLess(len(geo["features"]), 41060)
