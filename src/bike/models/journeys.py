import statistics
import multiprocessing
from contextlib import closing
from collections import defaultdict

import osmnx as ox

from bike.models.generic import GenericObjects
from bike import logger
from bike.models.journey import Journey
from bike.utils import (
    get_edge_colours,
    get_network_from_transport_type
)


def get_journey_edge_quality_map(journey):
    edge_quality_map = defaultdict(list)
    for edge_hash, edge_quality in journey.edge_quality_map.items():
        edge_quality_map[edge_hash].append(edge_quality)
    return edge_quality_map


class Journeys(GenericObjects):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('child_class', Journey)
        super().__init__(*args, **kwargs)

        network_types = [journey.network_type for journey in self]
        if len(set(network_types)) == 0 or len(set(network_types)) > 1:
            self.network_type = 'all'
        elif len(set(network_types)) == 1:
            self.network_type = network_types[0]

    @property
    def most_northern(self):
        """
        Get the most northerly latitude over all journeys
        """
        return max([journey.most_northern for journey in self])

    @property
    def most_southern(self):
        """
        Get the most southerly latitude over all journeys
        """
        return min([journey.most_southern for journey in self])

    @property
    def most_eastern(self):
        """
        Get the most easterly longitude over all journeys
        """
        return max([journey.most_eastern for journey in self])

    @property
    def most_western(self):
        """
        Get the most westerly longitude over all journeys
        """
        return min([journey.most_western for journey in self])

    @property
    def graph(self):
        """
        Get a graph that contains all journeys

        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        logger.debug(
            'Plotting bounding graph (n,s,e,w) (%s, %s, %s, %s)',
            self.most_northern,
            self.most_southern,
            self.most_eastern,
            self.most_western
        )
        return ox.graph_from_bbox(
            self.most_northern,
            self.most_southern,
            self.most_eastern,
            self.most_western,
            network_type=self.network_type,
            simplify=True
        )

    @staticmethod
    def from_files(filepaths):
        with closing(multiprocessing.Pool(multiprocessing.cpu_count())) as p:
            journeys = list(p.imap_unordered(Journey.from_file, filepaths))
        return Journeys(
            data=journeys
        )

    @property
    def edge_quality_map(self):
        """
        Get a map between edge_hash and road quality of the road. edge_map
        being edge id and road quality being something that hasn't been
        defined yet TODO

        :rtype: dict
        """

        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        journey_edge_quality_maps = pool.map(
            get_journey_edge_quality_map,
            self
        )

        # Use this when profiling
        #journey_edge_quality_maps = [get_journey_edge_quality_map(i) for i in self]

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

    def plot_routes(
        self,
        apply_condition_colour=False,
        use_closest_edge_from_base=False,
        min_edge_usage=1,
        colour_map_name='bwr',
        plot_kwargs={}
    ):
        """

        :kwarg apply_condition_colour: This is just a random colour for
            the moment as a jumping off point for when I come back to it
        :kwarg use_closest_from_base: For each point on the actual route, for
            each node use the closest node from the original base graph
            the route is being drawn on
        :kwargs min_edge_usage: The minimum number of times an edge has to be
            used for it to be included in the final data (1 per journey)
        :kwarg colour_map_name:
        :kwarg plot_kwargs: A dict of kwargs to pass to whatever plot is
            being done
        """
        if len(self) == 0:
            raise Exception('Current Journeys object has no content')
        if len(self) == 1:
            logger.warning('To use Journeys effectively multiple journeys must be used, only one found')

        base = self.graph
        if apply_condition_colour:
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
        else:
            if use_closest_edge_from_base:
                routes = [journey.closest_route for journey in self]
            else:
                routes = []
                for journey in self:
                    base.add_nodes_from(journey.route_graph.nodes(data=True))
                    base.add_edges_from(journey.route_graph.edges(data=True))
                    routes.append(journey.route)

            ox.plot_graph_routes(
                base,
                routes,
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
