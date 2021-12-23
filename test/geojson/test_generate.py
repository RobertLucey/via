from unittest import TestCase, skip

from via.geojson.generate import (
    get_generation_config,
    generate_geojson
)


class GeoJsonGenerateTest(TestCase):

    def test_get_generation_config(self):
        self.assertEqual(
            get_generation_config(),
            [
                {
                    'transport_type': 'all', 'name': 'all', 'version': None, 'version_op': None, 'earliest_time': None, 'latest_time': None, 'place': None
                },
                {
                    'transport_type': 'bike', 'name': 'bike', 'version': None, 'version_op': None, 'earliest_time': None, 'latest_time': None, 'place': None
                },
                {
                    'transport_type': 'car', 'name': 'car', 'version': None, 'version_op': None, 'earliest_time': None, 'latest_time': None, 'place': None
                },
                {
                    'transport_type': 'bus', 'name': 'bus', 'version': None, 'version_op': None, 'earliest_time': None, 'latest_time': None, 'place': None
                }
            ]
        )

        self.assertEqual(
            get_generation_config(transport_type='bike'),
            [
                {
                    'transport_type': 'bike', 'name': 'bike', 'version': None, 'version_op': None, 'earliest_time': None, 'latest_time': None, 'place': None
                }
            ]
        )

    @skip('todo')
    def test_generate_geojson(self):
        pass
