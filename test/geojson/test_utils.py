import datetime

from unittest import TestCase, skip

from via.geojson.utils import (
    parse_start_date,
    parse_end_date,
    geojson_from_graph,
)


class GeoJsonUtilTest(TestCase):
    def test_parse_start_date(self):
        with self.assertRaises(ValueError):
            parse_start_date(None)
        self.assertEqual(parse_start_date("2021-02-03"), "2021-02-03")
        self.assertEqual(parse_start_date("2021-02-03 01:02:03"), "2021-02-03")
        self.assertEqual(parse_start_date(datetime.date(2021, 2, 3)), "2021-02-03")
        self.assertEqual(
            parse_start_date(datetime.datetime(2021, 2, 3, 12)), "2021-02-03"
        )

    def test_parse_end_date(self):
        with self.assertRaises(ValueError):
            parse_end_date(None)
        self.assertEqual(parse_end_date("2021-02-03"), "2021-02-03")
        self.assertEqual(parse_end_date("2021-02-03 01:02:03"), "2021-02-03")
        self.assertEqual(parse_end_date(datetime.date(2021, 2, 3)), "2021-02-03")
        self.assertEqual(
            parse_end_date(datetime.datetime(2021, 2, 3, 12)), "2021-02-03"
        )

    @skip("todo")
    def test_geojson_from_graph(self):
        pass
