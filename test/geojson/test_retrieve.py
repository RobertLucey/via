from unittest import TestCase, skip

from via.geojson.retrieve import get_geojson


class GeoJsonRetrieveTest(TestCase):

    def test_get_geojson_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            get_geojson(
                'blahblah'
            )

    @skip('todo')
    def test_get_geojson_does_exist_too_old(self):
        pass

    @skip('todo')
    def test_get_geojson_does_exist_good_age(self):
        pass
