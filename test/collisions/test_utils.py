import shutil

from unittest import TestCase

from road_collisions.constants import COUNTY_MAP

from via.constants import GEOJSON_DIR
from via.models.collisions.collision import Collisions
from via.collisions.utils import (
    get_collisions,
    clean_filters,
    get_filters,
    retrieve_geojson,
    generate_geojson
)


class UtilTest(TestCase):

    def setUp(self):
        try:
            shutil.rmtree(GEOJSON_DIR)
        except FileNotFoundError:
            pass

    def test_get_collisions(self):
        self.assertGreater(
            len(get_collisions()),
            50000
        )
        self.assertIsInstance(
            get_collisions(),
            Collisions
        )

    def test_clean_filters(self):
        self.assertEqual(
            clean_filters(
                {
                    'something': None,
                    'something_else': 'all',
                    'something_other': 'blah'
                }
            ),
            {
                'something_other': 'blah'
            }
        )

    def test_get_filters(self):
        transport_types, counties, years_list = get_filters()

        self.assertEqual(transport_types, {None, 'bicycle', 'bus', 'car'})
        self.assertEqual(counties, list(COUNTY_MAP.values()))
        self.assertEqual(years_list, [None])

        transport_types, counties, years_list = get_filters(transport_type='bicycle', years=True, county='dublin')

        self.assertEqual(transport_types, {'bicycle'})
        self.assertEqual(counties, ['dublin'])
        self.assertEqual(years_list, [None, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005])

    def test_retrieve_geojson(self):

        modes = ['edge', 'point']

        for mode in modes:

            with self.assertRaises(FileNotFoundError):
                retrieve_geojson(
                    mode=mode,
                    county='leitrim',
                    transport_type='bicycle'
                )

            generate_geojson(
                mode=mode,
                county='leitrim',  # for quick loading
                transport_type='bicycle',
                only_used_regions=False
            )
            retrieve_geojson(
                mode=mode,
                county='leitrim',
                transport_type='bicycle'
            )

    def test_generate_geojson_points(self):
        points_geojson = generate_geojson(
            mode='point',
            county='dublin',
            transport_type='bicycle',
            only_used_regions=False
        )
        self.assertGreater(len(points_geojson['features']), 1000)

    def test_generate_geojson_lines(self):
        points_geojson = generate_geojson(
            mode='edge',
            county='leitrim',  # for quick loading
            transport_type='bicycle',
            only_used_regions=False
        )
        self.assertGreater(len(points_geojson['features']), 0)
