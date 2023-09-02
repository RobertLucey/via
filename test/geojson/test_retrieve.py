import os
import datetime

from unittest import TestCase, skip, skipUnless

from via.settings import GEOJSON_FILENAME_PREFIX
from via.geojson.retrieve import get_geojson
from via.db import db

from ..utils import wipe_mongo

IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class GeoJsonRetrieveTest(TestCase):
    def setUp(self):
        wipe_mongo()

    def tearDown(self):
        wipe_mongo()

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_geojson_not_exist(self):
        with self.assertRaises(LookupError):
            get_geojson("blahblah")

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_geojson_does_exist_too_old(self):
        with self.assertRaises(LookupError):
            data = {
                "journey_type": "bike",
                "geojson_version": "0.1.1",
                "geojson_version_op": None,
                "geojson_earliest_time": "2020-01-01",
                "geojson_latest_time": "2023-01-01",
                "geojson_place": None,
                "save_time": (
                    datetime.datetime.utcnow() - datetime.timedelta(days=365 * 10)
                ).timestamp(),
            }

            db.gridfs.put(
                "".encode("utf8"),
                metadata=data,
                filename=GEOJSON_FILENAME_PREFIX + "_something",
            )
            geojson = get_geojson("bike")

            raise Exception(geojson)

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_geojson_does_exist_good_age(self):
        data = {
            "journey_type": "bike",
            "geojson_version": "0.1.1",
            "geojson_version_op": None,
            "geojson_earliest_time": "2020-01-01",
            "geojson_latest_time": "2023-01-01",
            "geojson_place": None,
            "save_time": (
                datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
            ).timestamp(),
        }
        db.gridfs.put(
            "{}".encode("utf8"),
            metadata=data,
            filename=GEOJSON_FILENAME_PREFIX + "_something",
        )
        self.assertIsNotNone(get_geojson("bike"))
