from unittest import TestCase

import json
import random
import shutil
import os
import uuid
import time

from bike.models.journey import Journey
from bike.models.frame import Frame
from bike.utils import (
    is_journey_data_file,
    get_data_files,
    window,
    iter_journeys,
    sleep_until,
    get_idx_default,
    force_list,
    flatten
)

from bike.constants import (
    STAGED_DATA_DIR,
    SENT_DATA_DIR,
    DATA_DIR
)


@sleep_until(0.5)
def sleep_a_bit():
    return None


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
                        {'lat': random.random(), 'lng': random.random()},
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
                        {'lat': random.random(), 'lng': random.random()},
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

    def test_window(self):
        self.assertEqual(
            list(window([1, 2, 3, 4, 5])),
            [(1, 2), (2, 3), (3, 4), (4, 5)]
        )

        self.assertEqual(
            list(window([1, 2, 3, 4, 5], window_size=2)),
            [(1, 2), (2, 3), (3, 4), (4, 5)]
        )

        self.assertEqual(
            list(window([1, 2, 3, 4, 5], window_size=3)),
            [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        )

    def test_iter_journeys(self):

        starting_len = len(list(iter_journeys()))

        for i in range(4):
            journey = Journey()
            for i in range(1000):
                journey.append(
                    Frame(
                        0 + i,
                        {'lat': random.random(), 'lng': random.random()},
                        [random.random(), random.random(), random.random()],
                    )
                )
            journey.is_culled = False
            journey.save()

        self.assertEqual(
            len(list(iter_journeys())) - starting_len,
            4
        )

    def test_sleep_until(self):
        st = time.monotonic()
        sleep_a_bit()
        et = time.monotonic()
        taken = et - st

        self.assertTrue(taken >= 0.5)

    def test_get_idx_default(self):
        self.assertEqual(
            get_idx_default([1, 2, 3], 0, None),
            1
        )
        self.assertEqual(
            get_idx_default([1, 2, 3], 9, None),
            None
        )

    def test_force_list(self):
        self.assertEqual(
            force_list([]),
            []
        )
        self.assertEqual(
            force_list([[]]),
            [[]]
        )
        self.assertEqual(
            force_list(1),
            [1]
        )

    def test_flatten(self):
        self.assertEqual(
            flatten([[1, 2, 3], [1, 2]]),
            [1, 2, 3, 1, 2]
        )
