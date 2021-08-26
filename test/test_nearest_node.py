import json
import random

from mock import patch

import osmnx as ox

from unittest import TestCase

from via.nearest_node import NearestNodeCache
from via.models.frame import Frame, Frames


class NearestNodeTest(TestCase):

    def setUp(self):
        self.graph = ox.graph_from_place('Dublin, Ireland')
        self.points = [
            (-6.295029, 53.348127),
            (-6.259481, 53.344463),
            (-6.260696, 53.339891),
            (-6.258941, 53.346979)
        ]

    def test_get_nothing_cached(self):
        cache = NearestNodeCache()
        frames = []
        for point in self.points:
            frames.append(
                Frame(
                    0,
                    {'lat': point[1], 'lng': point[0]},
                    (0, 0, 0)
                )
            )

        self.assertEqual(
            cache.get(self.graph, frames),
            [12428414, 3451879900, 2893792091, 5101079533]
        )

    def test_get_some_cached(self):
        cache = NearestNodeCache()

        frames = []
        for point in random.sample(self.points, int(len(self.points) / 2)):
            frames.append(
                Frame(
                    0,
                    {'lat': point[1], 'lng': point[0]},
                    (0, 0, 0)
                )
            )
        cache.get(self.graph, frames)

        frames = []
        for point in self.points:
            frames.append(
                Frame(
                    0,
                    {'lat': point[1], 'lng': point[0]},
                    (0, 0, 0)
                )
            )
        self.assertEqual(
            cache.get(self.graph, frames),
            [12428414, 3451879900, 2893792091, 5101079533]
        )

    def test_get_all_cached(self):
        cache = NearestNodeCache()

        frames = []
        for point in self.points:
            frames.append(
                Frame(
                    0,
                    {'lat': point[1], 'lng': point[0]},
                    (0, 0, 0)
                )
            )
        self.assertEqual(
            cache.get(self.graph, frames),
            [12428414, 3451879900, 2893792091, 5101079533]
        )
        self.assertEqual(
            cache.get(self.graph, frames),
            [12428414, 3451879900, 2893792091, 5101079533]
        )
