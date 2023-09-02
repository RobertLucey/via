import os
import json
import re
from shutil import copyfile, rmtree

from unittest import TestCase, skip, skipUnless

from via.geojson.generate import generate_geojson

from via.db import db

from ..utils import wipe_mongo


IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class GeoJsonGenerateTest(TestCase):
    def setUp(self):
        wipe_mongo()

        if not IS_ACTION:
            with open("test/resources/raw_journey_data/1.json") as json_file:
                db.raw_journeys.insert_one(json.loads(json_file.read()))

    def tearDown(self):
        wipe_mongo()

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_generate_geojson(self):
        generate_geojson("bike")

        filename_pattern = re.compile("^test_")

        data = db.gridfs.find_one(
            {"metadata.journey_type": "bike", "filename": filename_pattern}
        )
        data = json.loads(data.read())

        self.assertGreater(len(data["features"]), 10)
        self.assertLess(len(data["features"]), 50)
