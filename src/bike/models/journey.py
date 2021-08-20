import statistics
from collections import defaultdict

import geopandas as gpd
import fast_json

from shapely.ops import cascaded_union

import networkx as nx
import osmnx as ox

from bike import logger
from bike.utils import (
    window,
    get_combined_id,
    get_edge_colours,
    get_network_from_transport_type
)
from bike.nearest_edge import nearest_edge
from bike.constants import POLY_POINT_BUFFER
from bike.models.point import FramePoint, FramePoints
from bike.models.frame import Frame
from bike.edge_cache import get_edge_data
from bike.network_cache import network_cache
from bike.models.journey_mixins import (
    SnappedRouteGraphMixin,
    GeoJsonMixin
)


class Journey(FramePoints, SnappedRouteGraphMixin, GeoJsonMixin):

    def __init__(self, *args, **kwargs):
        """

        :kwarg is_culled: If the journey is culled or not
        :kwarg transport_type: What transport type being used, defaults
            to settings.TRANSPORT_TYPE
        :kwarg suspension: If using suspension or not, defaults
            to settings.SUSPENSION
        """

        data = []
        if 'data' in kwargs:
            data = kwargs.pop('data')

        kwargs.setdefault('child_class', FramePoint)
        super().__init__(*args, **kwargs)

        self.extend(data)

        self.is_culled = kwargs.get('is_culled', False)
        self.is_sent = kwargs.get('is_sent', False)

        self.transport_type = kwargs.get('transport_type', None)
        self.suspension = kwargs.get('suspension', None)

        self.network_type = get_network_from_transport_type(
            self.transport_type
        )

        self.included_journeys = []

        self.last_gps = None

    def append(self, thing):
        """
        NB: appending needs to be chronological (can be reversed, just so
        long as it's consistent) as if no accelerometer data it assigns
        the accelerometer data to the previously seen gps

        Though journey data may not have time it will (should) always be
        chronological
        """
        # TODO: warn if not chronological
        if isinstance(thing, FramePoint):
            self._data.append(
                thing
            )
        else:
            frame = Frame.parse(thing)

            if not frame.gps.is_populated:
                if not hasattr(self, 'last_gps'):
                    return
                if self.last_gps is None:
                    return
                frame.gps = self.last_gps
            else:
                self.last_gps = frame.gps

            gps = frame.gps
            acc = frame.acceleration

            if len(self._data) == 0:
                self._data.append(
                    FramePoint(frame.time, gps, acc)
                )
                return

            if self._data[-1].gps == gps:
                self._data[-1].acceleration.append(acc)
            else:
                self._data.append(
                    FramePoint(frame.time, gps, acc)
                )

    @staticmethod
    def parse(objs):
        if isinstance(objs, Journey):
            return objs
        elif isinstance(objs, dict):
            return Journey(
                **objs
            )

        # TODO: do this from an object serialization
        raise NotImplementedError(
            'Can\'t parse journey from type %s' % (type(objs))
        )

    @staticmethod
    def from_file(filepath: str):
        """
        Given a file get a Journey object

        :param filepath: Path to a saved journey file
        :rtype: bike.models.journey.Journey
        """
        logger.debug('Loading journey from %s', filepath)
        with open(filepath, 'r') as journey_file:
            return Journey(
                **fast_json.loads(journey_file.read())
            )

    def get_indirect_distance(self, n_seconds=10):
        """
        NB: Data must be chronological

        :param n_seconds: use the location every n seconds as if the
            location is calculated too frequently the distance
            travelled could be artificially inflated
        :rtype: float
        :return: distance travelled in metres
        """
        previous_used_frame = None
        distances = []

        for frame in self:
            if previous_used_frame is None:
                previous_used_frame = frame
            elif frame.time >= previous_used_frame.time + n_seconds:
                distances.append(
                    previous_used_frame.distance_from(
                        frame
                    )
                )
                previous_used_frame = frame

        return sum(distances)

    def get_avg_speed(self, n_seconds=30):
        """
        NB: Data must be chronological

        :param n_seconds: use the location every n seconds as if the
                        location is calculated too frequently the distance
                        travelled could be artificially inflated
        :rtype: float
        :return: avg speed in metres per second
        """
        return self.get_indirect_distance(n_seconds=n_seconds) / self.duration

    def serialize(self, minimal=False, exclude_time=False):
        data = {
            'uuid': str(self.uuid),
            'data': super().serialize(exclude_time=exclude_time),
            'transport_type': self.transport_type,
            'suspension': self.suspension,
            'is_culled': self.is_culled,
            'is_sent': self.is_sent
        }

        if minimal is False:
            data.update(
                {
                    'direct_distance': self.direct_distance,
                    'indirect_distance': {
                        1: self.get_indirect_distance(n_seconds=1),
                        5: self.get_indirect_distance(n_seconds=5),
                        10: self.get_indirect_distance(n_seconds=10),
                        30: self.get_indirect_distance(n_seconds=30)
                    },
                    'data_quality': self.data_quality,
                    'duration': self.duration,
                    'avg_speed': self.get_avg_speed()
                }
            )

        return data

    def plot_route(
        self,
        apply_condition_colour=False,
        use_closest_edge_from_base=False,
        colour_map_name='bwr',
        plot_kwargs={}
    ):
        """

        :kwarg apply_condition_colour: This is just a random colour for
            the moment as a jumping off point for when I come back to it
        :kwarg use_closest_from_base: For each point on the actual route,
            for each node use the closest node from the original base graph
            the route is being drawn on
        :kwarg colour_map_name:
        :kwarg plot_kwargs: A dict of kwargs to pass to whatever plot is
            being done
        """
        base = self.graph
        if apply_condition_colour:

            if use_closest_edge_from_base:
                edge_colours = get_edge_colours(
                    base,
                    colour_map_name,
                    edge_map=self.edge_quality_map
                )

            else:
                base.add_nodes_from(self.route_graph.nodes(data=True))
                base.add_edges_from(self.route_graph.edges(data=True))

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
            raise NotImplementedError()

    @property
    def edge_quality_map(self):
        """
        Get a map between edge_hash and road quality of the road. edge_map
        being edge_id and road quality being something that hasn't been
        defined yet TODO

        :rtype: dict
        """
        data = {}
        for edge_id, single_edge_data in self.edge_data.items():
            data[edge_id] = {
                'avg': int(
                    statistics.mean(
                        [edge['avg_road_quality'] for edge in single_edge_data]
                    )
                ),
                'count': len(single_edge_data)
            }

        return data

    @property
    def edge_data(self):
        """

        :rtype: dict
        :return: {edge_id: [{edge_data}, {edge_data}]}
        """
        data = defaultdict(list)
        bounding_graph = self.graph
        route_graph = self.route_graph

        nearest_edge.get(bounding_graph, self._data, return_dist=False)

        for (our_origin, our_destination) in window(self, window_size=2):
            edge = nearest_edge.get(
                bounding_graph,
                [
                    our_origin
                ]
            )

            data[get_combined_id(edge[0][0], edge[0][1])].append(
                get_edge_data(
                    route_graph,
                    our_origin.uuid,
                    our_destination.uuid,
                )
            )

        nearest_edge.save()

        return data

    @property
    def closest_route(self):
        """
        Get the route but instead of creating new nodes from our journey
        data use the closest nodes on the bounding graph

        :rtype: list
        :return: list of node ids along the path
        """
        raise NotImplementedError()

    @property
    def route(self):
        """
        Get a list of nodes representing the journey.

        Only useful once route_graph is merged with a more detailed graph
        """
        raise NotImplementedError()

    @property
    def route_graph(self):
        """
        Get a graph of the journey without snapping to closest node / edge
        """
        graph = nx.Graph()

        combined_edge_data = defaultdict(list)

        for (origin, destination) in window(self, window_size=2):
            edge_id = get_combined_id(origin.uuid, destination.uuid)

            graph.add_node(
                origin.uuid,
                **{'x': origin.gps.lng, 'y': origin.gps.lat}
            )
            graph.add_node(
                destination.uuid,
                **{'x': destination.gps.lng, 'y': destination.gps.lat}
            )

            distance = origin.distance_from(destination)
            combined_edge_data[edge_id].append(
                {
                    'origin': origin,
                    'destination': destination,
                    'distance': distance,
                    'road_quality': origin.road_quality,
                    # TODO: other bits, speed / elevation maybe?
                }
            )

        merged_edge_data = {}
        for shared_id, values in combined_edge_data.items():
            merged_edge_data[shared_id] = {
                'origin': values[0]['origin'],
                'destination': values[0]['destination'],
                'distance': values[0]['distance'],
                'avg_road_quality': statistics.mean([val['road_quality'] for val in values]),
                'max_road_quality': max([val['road_quality'] for val in values])
            }

        for shared_id, values in merged_edge_data.items():
            graph.add_edge(
                values['origin'].uuid,
                values['destination'].uuid,
                length=values['distance'],
                avg_road_quality=values['avg_road_quality'],
                max_road_quality=values['max_road_quality']
            )

        return graph

    @property
    def bounding_graph(self):
        """
        Get a rectangular graph which contains the journey
        """
        logger.debug(
            'Plotting bounding graph (n,s,e,w) (%s, %s, %s, %s)',
            self.most_northern,
            self.most_southern,
            self.most_eastern,
            self.most_western
        )

        caches_key = 'bbox_journey_graph'

        if network_cache.get(caches_key, self.content_hash) is None:
            logger.debug(f'{caches_key} > {self.content_hash} not found in cache, generating...')
            network = ox.graph_from_bbox(
                self.most_northern,
                self.most_southern,
                self.most_eastern,
                self.most_western,
                network_type=self.network_type,
                simplify=True
            )
            network_cache.set(caches_key, self.content_hash, network)

        return network_cache.get(caches_key, self.content_hash)

    @property
    def graph(self):
        """
        Get a graph of the journey but excluding nodes far away from the route

        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        caches_key = 'poly_journey_graph'

        if network_cache.get(caches_key, self.content_hash) is None:
            logger.debug(f'{caches_key} > {self.content_hash} not found in cache, generating...')

            points = self.get_multi_points()

            buf = points.buffer(POLY_POINT_BUFFER, cap_style=3)
            boundary = gpd.GeoSeries(cascaded_union(buf))

            network = ox.graph_from_polygon(
                boundary.geometry[0],
                network_type=self.network_type,
                simplify=True
            )

            # TODO: might want to merge our edge_quality_data with edge data

            network_cache.set(caches_key, self.content_hash, network)

        return network_cache.get(caches_key, self.content_hash)

    @property
    def all_points(self):
        """
        Return all the points in this journey
        """
        return self._data
