import os

from unittest import TestCase, skip, skipUnless

from via.geojson.retrieve import get_geojson


IS_ACTION = os.environ.get('IS_ACTION', 'False') == 'True'


class GeoJsonRetrieveTest(TestCase):
    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_geojson_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            get_geojson("blahblah")

    @skip("todo")
    def test_get_geojson_does_exist_too_old(self):
        pass

    @skip("todo")
    def test_get_geojson_does_exist_good_age(self):
        pass
