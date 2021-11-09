import os
import time
from shutil import (
    copyfile,
    rmtree
)

from unittest import TestCase, skip

from via.collisions.utils import (
    get_collisions,
    clean_filters,
    get_filters,
    retrieve_geojson,
    generate_geojson
)


class UtilTest(TestCase):

    @skip('todo')
    def test_get_collisions(self):
        pass

    @skip('todo')
    def test_clean_filters(self):
        pass

    @skip('todo')
    def test_get_filters(self):
        pass

    @skip('todo')
    def test_retrieve_geojson_points(self):
        pass

    @skip('todo')
    def test_retrieve_geojson_lines(self):
        pass

    def test_generate_geojson_points(self):
        points_geojson = generate_geojson(
            mode='point',
            county='dublin',
            transport_type='bicycle'
        )
        self.assertGreater(len(points_geojson['features']), 1000)

    def test_generate_geojson_lines(self):
        points_geojson = generate_geojson(
            mode='edge',
            county='leitrim',  # for quick loading
            transport_type='bicycle'
        )
        self.assertGreater(len(points_geojson['features']), 0)
