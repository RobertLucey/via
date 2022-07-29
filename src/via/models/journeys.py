import statistics
import hashlib
import multiprocessing
from contextlib import closing
from collections import defaultdict
from typing import List

from networkx.classes.multidigraph import MultiDiGraph

from via.models.generic import GenericObjects
from via.models.journey import Journey
from via.utils import flatten
from via.models.journey_mixins import (
    SnappedRouteGraphMixin,
    GeoJsonMixin,
    BoundingGraphMixin
)


def get_journey_edge_quality_map(journey):
    edge_quality_map = defaultdict(list)
    for edge_hash, edge_quality in journey.edge_quality_map.items():
        edge_quality_map[edge_hash].append(edge_quality)

    return dict(edge_quality_map)


class Journeys(
    GenericObjects,
    SnappedRouteGraphMixin,
    GeoJsonMixin,
    BoundingGraphMixin
):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', Journey)
        super().__init__(*args, **kwargs)

        network_types = [journey.network_type for journey in self]
        if len(set(network_types)) == 0 or len(set(network_types)) > 1:
            self.network_type = 'all'
        elif len(set(network_types)) == 1:
            self.network_type = network_types[0]

    @property
    def edge_quality_map(self):
        """
        Get a map between edge_hash and road quality of the road. edge_map
        being edge id and road quality being something that hasn't been
        defined yet TODO

        :rtype: dict
        """

        #with multiprocessing.Pool(min([multiprocessing.cpu_count() - 1, 4])) as pool:
        #    journey_edge_quality_maps = pool.map(
        #        get_journey_edge_quality_map,
        #        self
        #    )

        journey_edge_quality_maps = [get_journey_edge_quality_map(i) for i in self]

        edge_quality_map = defaultdict(list)
        for journey_edge_quality_map in journey_edge_quality_maps:
            for edge_id, quals in journey_edge_quality_map.items():
                edge_quality_map[edge_id].extend(quals)

        return {
            edge_id: {
                'avg': int(statistics.mean([d['avg'] for d in data])),
                'count': len(data),
                'edge_id': edge_id,
                'speed': statistics.mean([val['speed'] for val in data]) if None not in [val['speed'] for val in data] else None,
                'collisions': flatten([[i.serialize() for i in v['collisions']] for v in data])
            } for edge_id, data in edge_quality_map.items()
        }

    @property
    def most_northern(self) -> float:
        """
        Get the most northerly latitude over all journeys
        """
        return max([journey.most_northern for journey in self])

    @property
    def most_southern(self) -> float:
        """
        Get the most southerly latitude over all journeys
        """
        return min([journey.most_southern for journey in self])

    @property
    def most_eastern(self) -> float:
        """
        Get the most easterly longitude over all journeys
        """
        return max([journey.most_eastern for journey in self])

    @property
    def most_western(self) -> float:
        """
        Get the most westerly longitude over all journeys
        """
        return min([journey.most_western for journey in self])

    def get_graph(self, use_graph_cache=True):
        return self.get_bounding_graph(use_graph_cache=use_graph_cache)

    @property
    def graph(self) -> MultiDiGraph:
        return self.get_graph(use_graph_cache=True)

    @staticmethod
    def from_files(filepaths):
        with closing(multiprocessing.Pool(multiprocessing.cpu_count() - 1)) as pool:
            journeys = list(pool.imap_unordered(Journey.from_file, filepaths))
        return Journeys(
            data=journeys
        )

    @property
    def gps_hash(self) -> str:
        return hashlib.md5(
            str([
                journey.gps_hash for journey in self
            ]).encode()
        ).hexdigest()

    @property
    def content_hash(self) -> str:
        return hashlib.md5(
            str([
                journey.content_hash for journey in self
            ]).encode()
        ).hexdigest()

    @property
    def all_points(self) -> List:
        """
        Return all the points in this journeys obj
        """
        return flatten([journey.all_points for journey in self._data])

    @property
    def bbox(self):
        return {
            'north': self.most_northern,
            'south': self.most_southern,
            'east': self.most_eastern,
            'west': self.most_western
        }

    @property
    def regions(self):
        return [journey.region for journey in self]
