import os
import json
import hashlib
import statistics
from collections import defaultdict

import reverse_geocoder
import geopandas as gpd
import fast_json

import shapely
from shapely.ops import cascaded_union

import networkx as nx
import osmnx as ox
from networkx.readwrite import json_graph

from bike import logger
from bike.utils import (
    window,
    get_combined_id,
    get_edge_colours,
    get_network_from_transport_type,
    filter_nodes_from_geodataframe,
    filter_edges_from_geodataframe,
    update_edge_data
)
from bike.nearest_edge import nearest_edge
from bike.constants import (
    POLY_POINT_BUFFER,
    GEOJSON_DIR
)
from bike.models.point import FramePoint, FramePoints
from bike.models.frame import Frame
from bike.edge_cache import get_edge_data
from bike.place_cache import place_cache
from bike.network_cache import network_cache


class Journey(FramePoints):

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

    @property
    def country(self):
        """
        Get what country this journey started in

        :return: a two letter country code
        :rtype: str
        """
        return reverse_geocoder.search(
            (
                self.origin.gps.lat,
                self.origin.gps.lng
            )
        )[0]['cc']

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

        :param n_seconds: use the location every n seconds as if the
                        location is calculated too frequently the distance
                        travelled could be artificially inflated
        :rtype: float
        :return: avg speed in metres per second
        """
        return self.get_indirect_distance(n_seconds=n_seconds) / self.duration

    def is_in_place(self, place_name: str):
        """
        Get if a journey is entirely within the bounds of some place.
        Does this by rect rather than polygon so it isn't exact but mainly
        to be used to focus on a single city.

        :param place_name: An osmnx place name. For example "Dublin, Ireland"
            To see if the place name is valid try graph_from_place(place).
            Might be good to do that in here and throw an ex if it's not found
        """
        place_bounds = place_cache.get(place_name)
        try:
            return all([
                self.most_northern < place_bounds['north'],
                self.most_southern > place_bounds['south'],
                self.most_eastern < place_bounds['east'],
                self.most_western > place_bounds['west']
            ])
        except ValueError:
            return False

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

        # FIXME: This uses nodes to get edges, should use nearest edge
        # unless very close to a node. Factor in direction and all that

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
    def content_hash(self):
        return hashlib.md5(
            str([
                point.serialize() for point in self
            ]).encode()
        ).hexdigest()

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
    def snapped_route_graph(self):
        """
        Get the route graph, snapping to the nearest edge
        """
        bounding_graph = self.graph

        nearest_edge.get(bounding_graph, self._data, return_dist=False)

        edges = []
        used_node_ids = []
        for (our_origin, our_destination) in window(self, window_size=2):
            edge = nearest_edge.get(
                bounding_graph,
                [
                    our_origin
                ]
            )
            edges.append(tuple(edge[0]))
            used_node_ids.extend([edge[0][0], edge[0][1]])

        graph_nodes, graph_edges = ox.graph_to_gdfs(
            bounding_graph,
            fill_edge_geometry=True
        )

        # Filter only the nodes and edges on the route and ignore the
        # buffer used to get context
        graph = ox.graph_from_gdfs(
            filter_nodes_from_geodataframe(graph_nodes, used_node_ids),
            filter_edges_from_geodataframe(graph_edges, edges)
        )

        graph = update_edge_data(graph, self.edge_quality_map)

        return graph

    @property
    def geojson(self):
        """
        Write and return a GeoJSON object string of the graph.
        """
        geojson_file = os.path.join(
            GEOJSON_DIR,
            self.content_hash + '.geojson'
        )

        if os.path.exists(geojson_file):
            geojson_features = None
            with open(geojson_file, 'r') as json_file:
                geojson_features = fast_json.loads(json_file.read())
        else:
            json_links = json_graph.node_link_data(
                self.snapped_route_graph
            )['links']

            geojson_features = {
                'type': 'FeatureCollection',
                'features': []
            }

            for link in json_links:
                if 'geometry' not in link:
                    continue

                feature = {
                    'type': 'Feature',
                    'properties': {}
                }

                for k in link:
                    if k == 'geometry':
                        feature['geometry'] = shapely.geometry.mapping(
                            link['geometry']
                        )
                    else:
                        feature['properties'][k] = link[k]

                geojson_features['features'].append(feature)

            if not os.path.exists(geojson_file):
                os.makedirs(
                    os.path.join(GEOJSON_DIR),
                    exist_ok=True
                )

            with open(geojson_file, 'w') as json_file:
                json.dump(
                    geojson_features,
                    json_file,
                    indent=4
                )

        return geojson_features
