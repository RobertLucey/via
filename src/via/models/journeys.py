import statistics
import hashlib
import multiprocessing
from contextlib import closing
from collections import defaultdict
from typing import List

import osmnx as ox
from networkx.classes.multidigraph import MultiDiGraph

from via.models.generic import GenericObjects
from via import logger
from via.models.journey import Journey
from via.utils import (
    get_edge_colours,
    flatten
)
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

    def plot_routes(
        self,
        use_graph_cache=False,
        use_closest_edge_from_base=False,
        min_edge_usage=1,
        colour_map_name='bwr',
        plot_kwargs=None
    ):
        """

        :kwarg use_closest_from_base: For each point on the actual route, for
            each node use the closest node from the original base graph
            the route is being drawn on
        :kwargs min_edge_usage: The minimum number of times an edge has to be
            used for it to be included in the final data (1 per journey)
        :kwarg colour_map_name:
        :kwarg plot_kwargs: A dict of kwargs to pass to whatever plot is
            being done
        """
        if plot_kwargs is None:
            plot_kwargs = {}
        if len(self) == 0:
            raise Exception('Current Journeys object has no content')
        if len(self) == 1:
            logger.warning('To use Journeys effectively multiple journeys must be used, only one found')

        base = self.get_graph(use_graph_cache=use_graph_cache)
        if use_closest_edge_from_base:
            edge_colours = get_edge_colours(
                base,
                colour_map_name,
                edge_map={
                    edge_id: data for edge_id, data in self.edge_quality_map.items() if data['count'] >= min_edge_usage
                }
            )
        else:
            for journey in self:
                base.add_nodes_from(journey.route_graph.nodes(data=True))
                base.add_edges_from(journey.route_graph.edges(data=True))

            edge_colours = get_edge_colours(
                base,
                colour_map_name,
                key_name='avg_road_quality'
            )

        ox.plot_graph(
            base,
            edge_color=edge_colours,
            **plot_kwargs
        )

    def get_mega_journeys(self):
        megas = defaultdict(Journey)

        for journey in self:
            key = '%s_%s' % (journey.transport_type, journey.suspension)
            megas[key].extend([frame for frame in journey])
            megas[key].transport_type = journey.transport_type
            megas[key].suspension = journey.suspension
            megas[key].included_journeys.append(journey)

        return megas

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
                'count': len(data)
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
