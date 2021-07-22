from unittest import TestCase

import json
import random
import shutil
import os
import uuid

from bike.models.journey import Journey
from bike.models.frame import Frame
from bike.utils import (
    is_journey_data_file,
    get_data_files,
    journey_from_file
)

from bike.constants import (
    STAGED_DATA_DIR,
    SENT_DATA_DIR,
    DATA_DIR
)


class UtilTest(TestCase):

    def setUp(self):

        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)

        os.makedirs(STAGED_DATA_DIR, exist_ok=True)
        os.makedirs(SENT_DATA_DIR, exist_ok=True)

        staged_ids = [str(uuid.uuid4()) for _ in range(10)]
        sent_ids = [str(uuid.uuid4()) for _ in range(20)]

        for staged_id in staged_ids:
            fp = os.path.join(STAGED_DATA_DIR, staged_id + '.json')

            journey = Journey()

            for i in range(random.randint(100, 2000)):
                journey.append(
                    Frame(
                        0 + i,
                        (random.random(), random.random()),
                        (random.random(), random.random(), random.random()),
                    )
                )

            with open(fp, 'w') as f:
                json.dump(journey.serialize(minimal=True), f)

        for sent_id in sent_ids:
            fp = os.path.join(SENT_DATA_DIR, sent_id + '.json')

            journey = Journey()

            for i in range(random.randint(100, 2000)):
                journey.append(
                    Frame(
                        0 + i,
                        (random.random(), random.random()),
                        (random.random(), random.random(), random.random()),
                    )
                )

            with open(fp, 'w') as f:
                json.dump(journey.serialize(minimal=True), f)

    def test_get_data_files(self):

        data_files = get_data_files()
        self.assertEqual(len(data_files), 30)

        data_files = get_data_files(staged=True)
        self.assertEqual(len(data_files), 10)

        data_files = get_data_files(staged=False)
        self.assertEqual(len(data_files), 20)

    def test_is_journey_data_file(self):

        data_files = get_data_files()

        test_file = data_files[0]

        self.assertTrue(
            is_journey_data_file(test_file)
        )

        self.assertFalse(
            is_journey_data_file('/dev/null')
        )

    def test_journey_from_file(self):

        journey = Journey()

        for i in range(1000):
            journey.append(
                Frame(
                    0 + i,
                    [random.random(), random.random()],
                    [random.random(), random.random(), random.random()],
                )
            )

        journey.save()

        new_journey = journey_from_file(journey.filepath)

        self.assertEquals(journey.serialize(), new_journey.serialize())
