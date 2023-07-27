import os
import json
from shutil import copyfile, rmtree

from unittest import TestCase, skip, skipUnless

from via.geojson.generate import get_generation_config, generate_geojson

from via.settings import (
    MONGO_RAW_JOURNEYS_COLLECTION,
    MONGO_NETWORKS_COLLECTION,
    MONGO_PARSED_JOURNEYS_COLLECTION,
)

from via.utils import get_mongo_interface


IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


class GeoJsonGenerateTest(TestCase):
    def setUp(self):
        with open("test/resources/raw_journey_data/1.json") as json_file:
            getattr(get_mongo_interface(), MONGO_RAW_JOURNEYS_COLLECTION).insert_one(
                json.loads(json_file.read())
            )

    def tearDown(self):
        getattr(get_mongo_interface(), MONGO_RAW_JOURNEYS_COLLECTION).drop()
        getattr(get_mongo_interface(), MONGO_NETWORKS_COLLECTION).drop()
        getattr(get_mongo_interface(), MONGO_PARSED_JOURNEYS_COLLECTION).drop()

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_get_generation_config(self):
        self.assertEqual(
            get_generation_config(),
            [
                {
                    "transport_type": "all",
                    "name": "all",
                    "version": None,
                    "version_op": None,
                    "earliest_time": None,
                    "latest_time": None,
                    "place": None,
                },
                {
                    "transport_type": "bike",
                    "name": "bike",
                    "version": None,
                    "version_op": None,
                    "earliest_time": None,
                    "latest_time": None,
                    "place": None,
                },
                {
                    "transport_type": "car",
                    "name": "car",
                    "version": None,
                    "version_op": None,
                    "earliest_time": None,
                    "latest_time": None,
                    "place": None,
                },
                {
                    "transport_type": "bus",
                    "name": "bus",
                    "version": None,
                    "version_op": None,
                    "earliest_time": None,
                    "latest_time": None,
                    "place": None,
                },
            ],
        )

        self.assertEqual(
            get_generation_config(transport_type="bike"),
            [
                {
                    "transport_type": "bike",
                    "name": "bike",
                    "version": None,
                    "version_op": None,
                    "earliest_time": None,
                    "latest_time": None,
                    "place": None,
                }
            ],
        )

    @skipUnless(not IS_ACTION, "action_mongo")
    def test_generate_geojson(self):
        generate_geojson("bike")

        data = list(
            getattr(get_mongo_interface(), MONGO_PARSED_JOURNEYS_COLLECTION).find()
        )

        self.assertEqual(len(data), 1)

        data = data[0]

        self.assertGreater(len(data["features"]), 10)
        self.assertLess(len(data["features"]), 50)
