import pickle

from unittest import TestCase

from via.nearest_edge import NearestEdgeCache
from via.models.point import FramePoint


class NearestEdgeTest(TestCase):

    def setUp(self):
        with open('test/resources/dublin_graph.pickle', 'rb') as f:
            self.graph = pickle.load(f)

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

        print(f'Edges pre: {edges}')
        edges = [list(edges[0][0]) for i in edges]
        print(f'Edges post: {edges}')
        self.assertTrue(
            (12428414, 4161475238, 0) in edges[0] or (4161475238, 12428414, 0) in edges[0] or [12428414, 4161475238, 0] in edges[0] or [4161475238, 12428414, 0] in edges[0]
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
        cache = NearestEdgeCache()
        cache.load()
        print(cache.data.keys())
        self.assertTrue('489334746920999497411653940021' in cache.data.keys())
