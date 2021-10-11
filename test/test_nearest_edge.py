import json
import random

from mock import patch

import osmnx as ox

from unittest import TestCase

from via.nearest_edge import NearestEdgeCache
from via.models.frame import Frame, Frames
from via.models.point import FramePoint


class NearestEdgeTest(TestCase):

    def setUp(self):
        self.graph = ox.graph_from_place('Dublin, Ireland')

    def test_get(self):
        cache = NearestEdgeCache()
        edges = cache.get(
            self.graph,
            [
                FramePoint.parse(
                    {
                        'time': 0,
                        'gps': {'lat': 53.348127, 'lng': -6.295029},
                        'acc': [0, 0, 0]
                    }
                )
            ]
        )

        edges = [list(edges[0][0]) for i in edges]
        self.assertTrue(
            [12428414, 4161475238, 0] in edges or [4161475238, 12428414, 0] in edges
        )

    def test_save_load(self):
        cache = NearestEdgeCache()
        cache.get(
            self.graph,
            [
                FramePoint.parse(
                    {
                        'time': 0,
                        'gps': {'lat': 53.348127, 'lng': -6.295029},
                        'acc': [0, 0, 0]
                    }
                )
            ]
        )
        cache.save()

        cache = NearestEdgeCache()
        self.assertEqual(cache.data, {})
        cache.load()
        self.assertTrue('489334746920999497411653940021' in cache.data.keys())
