import datetime
import statistics

from collections import defaultdict
from functools import lru_cache
from packaging import version

from dateutil.parser import parse

from cached_property import cached_property
import geopandas as gpd
import fast_json

from shapely.ops import cascaded_union

import networkx as nx
import osmnx as ox

from via import settings
from via import logger
from via.utils import (
    window,
    get_combined_id
)
from via.nearest_edge import nearest_edge
from via.constants import POLY_POINT_BUFFER
from via.models.point import FramePoint, FramePoints
from via.models.frame import Frame
from via.edge_cache import get_edge_data
from via.network_cache import network_cache
from via.models.journey_mixins import (
    SnappedRouteGraphMixin,
    GeoJsonMixin,
    BoundingGraphMixin
)
from via.collision_edge_cache import collision_edge_cache
from via.models.collisions.collision import COLLISIONS


class Journey(
    FramePoints,
    SnappedRouteGraphMixin,
    GeoJsonMixin,
    BoundingGraphMixin
):

    def __init__(self, *args, **kwargs):
        """

        :kwarg is_culled: If the journey is culled or not
        :kwarg transport_type: What transport type being used, defaults
            to settings.TRANSPORT_TYPE
        :kwarg suspension: If using suspension or not, defaults
            to settings.SUSPENSION
        """
        self.gps_inclusion_iter = 0
        self.too_slow = False

        data = []
        if 'data' in kwargs:
            data = kwargs.pop('data')

        kwargs.setdefault('child_class', FramePoint)
        super().__init__(*args, **kwargs)

        self.extend(data)

        self._version = kwargs.get('version', None)

        self.is_culled = kwargs.get('is_culled', False)
        self.is_sent = kwargs.get('is_sent', False)

        self.transport_type = str(
            kwargs.get('transport_type', 'unknown')
        ).lower()
        self.suspension = kwargs.get('suspension', None)

        self.network_type = kwargs.get('network_type', 'all')
        self._timestamp = kwargs.get('timestamp', None)

        self.included_journeys = []

        self.last_gps = None

    def __del__(self):
        attrs_to_del = [
            'edge_quality_map',
            'route_graph'
        ]

        for attr in attrs_to_del:
            try:
                delattr(self, attr)
            except:
                pass

    @staticmethod
    def parse(objs):
        if isinstance(objs, Journey):
            return objs

        if isinstance(objs, dict):
            return Journey(
                **objs
            )

        raise NotImplementedError(
            f'Can\'t parse journey from type {type(objs)}'
        )

    @staticmethod
    @lru_cache(maxsize=500)
    def from_file(filepath: str):
        """
        Given a file get a Journey object

        :param filepath: Path to a saved journey file
        :rtype: via.models.journey.Journey
        """
        logger.debug('Loading journey from %s', filepath)

        # TODO: should cache stages of processed files from raw (currently,
        # which uses frames instead of frame points) to processed (which
        # it will use frame points) so we can skip the building up of context
        # when we should be able to find from a raw file path

        with open(filepath, 'r') as journey_file:
            return Journey(
                **fast_json.loads(journey_file.read())
            )

    def set_contexts(self):
        for (one, two, three, four, five, six, seven) in window(self, window_size=7):
            if not four.is_context_populated:
                four.set_context(
                    pre=[one, two, three],
                    post=[five, six, seven]
                )

    def extend(self, objs):
        for obj in objs:
            self.append(obj, set_contexts=False)
        self.set_contexts()

    def append(self, obj, set_contexts=True):
        """
        NB: appending needs to be chronological (can be reversed, just so
        long as it's consistent) as if no accelerometer data it assigns
        the accelerometer data to the previously seen gps

        Though journey data may not have time it will (should) always be
        chronological
        """
        # TODO: warn if not chronological
        if isinstance(obj, FramePoint):
            self._data.append(
                obj
            )
        else:
            # Most datapoints are only accelerometer so we need to find the
            # closest point with gps in the past to add the accelerometer
            # data to

            frame = Frame.parse(obj)

            frame_gps_populated = frame.gps.is_populated

            if frame_gps_populated:
                if self.gps_inclusion_iter % settings.GPS_INCLUDE_RATIO == 0:
                    self.last_gps = frame.gps
                else:
                    frame.gps = self.last_gps
                self.gps_inclusion_iter += 1
            else:
                if not hasattr(self, 'last_gps'):
                    return
                if self.last_gps is None:
                    return
                frame.gps = self.last_gps

            if len(self._data) == 0:
                self._data.append(
                    FramePoint(frame.time, frame.gps, frame.acceleration)
                )
                return

            # Remove points that are too slow / fast in relation to
            # the previous point
            if (frame_gps_populated or frame.gps.is_populated) and frame.time is not None:
                metres_per_second = self._data[-1].speed_between(frame)
                if metres_per_second is not None:
                    if any([
                        metres_per_second < settings.MIN_METRES_PER_SECOND,
                        metres_per_second > settings.MAX_METRES_PER_SECOND
                    ]):
                        self.too_slow = True
                    else:
                        self.too_slow = False

            if self.too_slow:
                # Append a framepoint but don't put any accelerometer
                # data in it so we can use it for speed but not for quality

                #self._data.append(
                #    FramePoint(frame.time, frame.gps, frame.acceleration)
                #)

                return

            if self._data[-1].gps == frame.gps:
                self._data[-1].append_acceleration(frame.acceleration)
            else:
                self._data.append(
                    FramePoint(frame.time, frame.gps, frame.acceleration)
                )

        if set_contexts:
            self.set_contexts()

    def get_indirect_distance(self, n_seconds: int = 10) -> float:
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

    def get_avg_speed(self, n_seconds: int = 30) -> float:
        """
        NB: Data must be chronological

        :param n_seconds: use the location every n seconds as if the
                        location is calculated too frequently the distance
                        travelled could be artificially inflated
        :rtype: float
        :return: avg speed in metres per second
        """
        return self.get_indirect_distance(n_seconds=n_seconds) / self.duration

    def serialize(
        self,
        minimal: bool = False,
        include_time: bool = True,
        include_context: bool = True
    ):
        data = {
            'uuid': str(self.uuid),
            'version': str(self.version),
            'data': super().serialize(include_time=include_time, include_context=include_context),
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

    @property
    def timestamp(self):
        if self._timestamp is None:
            # FIXME: We shouldn't need to do this but the ui always includes earliest / latest as a filter
            return datetime.datetime(2021, 1, 1)
        return parse(self._timestamp)

    @cached_property
    def edge_quality_map(self):
        """
        Get a map between edge_hash and road quality of the road. edge_map
        being edge_id and road quality being something that hasn't been
        defined yet TODO

        :rtype: dict
        """

        # FIXME: this is very lazy making sure at least some collisions have been generated
        from via.constants import COLLISION_EDGE_CACHE_DIR
        if len(collision_edge_cache.data) == 0:
            from via.collisions.utils import generate_geojson
            generate_geojson(
                transport_type='bicycle',
                years=False,
                county=None,
                mode='edge',
                only_used_regions=True
            )

        data = {}
        for edge_id, single_edge_data in self.edge_data.items():
            qualities = [edge['avg_road_quality'] for edge in single_edge_data]
            speed = statistics.mean([val['speed'] for val in single_edge_data]) if None not in [val['speed'] for val in single_edge_data] else None
            if len(qualities) == 0:
                data[edge_id] = {
                    'avg': 0,
                    'count': 0,
                    'speed': speed,
                    'collisions': []
                }
            else:
                data[edge_id] = {
                    'avg': int(
                        statistics.mean(
                            qualities
                        )
                    ),
                    'count': len(qualities),
                    'speed': speed,
                    'collisions': COLLISIONS.get_by_gps_hash(
                        tuple(collision_edge_cache.get(edge_id))
                    )
                }

        return {
            edge_id: d for edge_id, d in data.items() if d['count'] >= settings.MIN_PER_JOURNEY_USAGE
        }

    @property
    def edge_data(self):
        """

        :rtype: dict
        :return: {edge_id: [{edge_data}, {edge_data}]}
        """
        data = defaultdict(list)
        bounding_graph = self.graph
        route_graph = self.route_graph

        nearest_edge.get(bounding_graph, self._data)

        raw_edges_list = []
        for (our_origin, our_destination) in window(self, window_size=2):
            nearest_edges = nearest_edge.get(
                bounding_graph,
                [
                    our_origin
                ]
            )[0]

            edge = our_origin.get_best_edge(
                nearest_edges,
                mode=settings.NEAREST_EDGE_METHOD,
                graph=bounding_graph
            )

            our_edge_data = get_edge_data(
                our_origin.uuid,
                our_destination.uuid,
                graph=route_graph
            )

            raw_edges_list.append(
                [
                    get_combined_id(edge[0][0], edge[0][1]),
                    our_edge_data
                ]
            )

        edges_list = []
        for (pre, current, post) in window(raw_edges_list, window_size=3):
            if pre[0] == post[0] and current[0] != pre[0]:
                current[0] = pre[0]
            edges_list.append(current)

        for edge in edges_list:
            data[edge[0]].append(
                edge[1]
            )

        return data

    @cached_property
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
                    'speed': (origin.speed + destination.speed) / 2 if (origin.speed is not None and destination.speed is not None) else None
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
                'max_road_quality': max([val['road_quality'] for val in values]),
                'speed': statistics.mean([val['speed'] for val in values]) if None not in [val['speed'] for val in values] else None
            }

        for shared_id, values in merged_edge_data.items():
            graph.add_edge(
                values['origin'].uuid,
                values['destination'].uuid,
                length=values['distance'],
                avg_road_quality=values['avg_road_quality'],
                max_road_quality=values['max_road_quality'],
                speed=values['speed']
            )

        return graph

    @property
    def bbox(self) -> dict:
        return {
            'north': self.most_northern,
            'south': self.most_southern,
            'east': self.most_eastern,
            'west': self.most_western
        }

    @property
    def poly_graph(self):
        """
        Get a graph of the journey but excluding nodes far away from the route

        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """

        if network_cache.get('poly', self) is None:
            logger.debug('poly > %s not found in cache, generating...', self.gps_hash)

            # TODO: might want to not use polygon for this since we could
            # get the benefits of using a parent bbox from the cache

            # Maybe use city if possible and then truncate_graph_polygon
            points = self.get_multi_points()

            buf = points.buffer(POLY_POINT_BUFFER, cap_style=3)
            boundary = gpd.GeoSeries(cascaded_union(buf))

            network = ox.graph_from_polygon(
                boundary.geometry[0],
                network_type=self.network_type,
                simplify=True
            )

            # TODO: might want to merge our edge_quality_data with
            # edge data here

            network_cache.set('poly', self, network)

        return network_cache.get('poly', self)

    @property
    def graph(self):
        """
        Get a graph of the journey but excluding nodes far away from the route

        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        return self.bounding_graph

    @property
    def all_points(self):
        """
        Return all the points in this journey.

        May be a bit expensive since it sets contexts. Can probably get away
        with selectively doing this
        """
        self.set_contexts()
        return self._data

    @property
    def version(self):
        """
        Get the version of the app used to generate this data

        :rtype: version.Version
        """
        if isinstance(self._version, version.Version):
            return self._version
        if isinstance(self._version, type(None)):
            return version.parse('0.0.0')
        return version.parse(self._version)

    @property
    def region(self):
        return self.origin.gps.reverse_geo['place_2']
