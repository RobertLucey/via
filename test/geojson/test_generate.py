import os
import json
from shutil import copyfile, rmtree

from unittest import TestCase, skip

from via.geojson.generate import get_generation_config, generate_geojson
from via.constants import REMOTE_DATA_DIR, DATA_DIR, GEOJSON_DIR


class GeoJsonGenerateTest(TestCase):
    def setUp(self):
        try:
            rmtree(DATA_DIR)
        except Exception as ex:
            pass

        os.makedirs(REMOTE_DATA_DIR + "/bike", exist_ok=True)
        copyfile(
            "test/resources/raw_journey_data/1.json",
            os.path.join(REMOTE_DATA_DIR, "bike/1.json"),
        )
        copyfile(
            "test/resources/raw_journey_data/2.json",
            os.path.join(REMOTE_DATA_DIR, "bike/2.json"),
        )

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

    def test_generate_geojson(self):
        generate_geojson("bike")

        data = None
        with open(
            os.path.join(
                GEOJSON_DIR,
                "transport_type=bike&earliest_time=2021-01-01&latest_time=2023-12-31.geojson",
            ),
            "r",
        ) as f:
            data = json.loads(f.read())

        self.assertGreater(len(data["features"]), 10)
        self.assertLess(len(data["features"]), 50)
