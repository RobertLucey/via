import hashlib
import urllib
import os
import glob
from multiprocessing import (
    Pool,
    cpu_count
)
from multiprocessing.dummy import Pool as ThreadPool
from itertools import groupby
from operator import itemgetter
from collections import defaultdict

from cached_property import cached_property
from haversine import (
    haversine,
    Unit
)
import fast_json

import osmnx as ox

from road_collisions.models.raw_collision import RawCollision as BaseRawCollision
from road_collisions.models.collision import Collision as BaseCollision
from road_collisions.models.collision import Collisions as BaseCollisions

from via import logger
from via.constants import GEOJSON_DIR
from via.nearest_edge import nearest_edge
from via.constants import METRES_PER_DEGREE
from via.utils import (
    area_from_coords,
    get_graph_id,
    filter_nodes_from_geodataframe,
    filter_edges_from_geodataframe,
    update_edge_data,
    get_combined_id
)
from via.network_cache import network_cache
from via.models.gps import GPSPoint
from via.bounding_graph_gdfs_cache import bounding_graph_gdfs_cache
from via.geojson.utils import geojson_from_graph


class Collision(BaseCollision):

    def __del__(self):
        attrs_to_del = [
            'gps_hash',
            'lat_span',
            'lng_span',
            'upper_left_bbox',
            'upper_right_bbox',
            'lower_left_bbox',
            'lower_right_bbox'
        ]

        for attr in attrs_to_del:
            try:
                delattr(self, attr)
            except:
                pass

    @staticmethod
    def parse(data):
        if isinstance(data, Collision):
            return data

        if isinstance(data, dict):
            if 'data' in data.keys():
                return Collision(
                    **BaseRawCollision.parse(
                        data
                    ).data
                )
            else:
                # from serialization
                return Collision(
                    **data
                )

    @property
    def gps(self):
        return GPSPoint(
            self.lat,
            self.lng
        )

    @cached_property
    def gps_hash(self):
        return self.gps.content_hash

    def is_in_place(self, place_bounds):
        return all([
            self.lat < place_bounds['north'],
            self.lat > place_bounds['south'],
            self.lng < place_bounds['east'],
            self.lng > place_bounds['west']
        ])


class Collisions(BaseCollisions):

    def __init__(self, *args, **kwargs):
        """

        :kwarg filters: Filters to apply, these filters will apply inplace
            as a relevant action is made
        """
        self.filters = kwargs.get('filters', {})
        self.is_filtered = kwargs.get('is_filtered', False)
        super().__init__(*args, **kwargs)

    def set_filters(self, filters):
        self.filters = filters

    @property
    def danger(self):
        # FIXME: generally improve
        return len(self)

    @property
    def danger_by_vehicle_type(self):

        type_collisions = [
            (c.vehicle_type, c) for c in self
        ]

        d = defaultdict(Collisions)
        for x, y in type_collisions:
            d[x].append(y)

        return {
            k: v.danger for k, v in d.items()
        }

    @property
    def most_northern(self):
        return max([collision.gps.lat for collision in self])

    @property
    def most_southern(self):
        return min([collision.gps.lat for collision in self])

    @property
    def most_eastern(self):
        return max([collision.gps.lng for collision in self])

    @property
    def most_western(self):
        return min([collision.gps.lng for collision in self])

    @property
    def bbox(self):
        return {
            'north': self.most_northern,
            'south': self.most_southern,
            'east': self.most_eastern,
            'west': self.most_western
        }

    @cached_property
    def lat_span(self):
        return haversine(
            (self.most_northern, 0),
            (self.most_southern, 0),
            unit=Unit.METERS
        )

    @cached_property
    def lng_span(self):
        return haversine(
            (0, self.most_western),
            (0, self.most_eastern),
            unit=Unit.METERS
        )

    @cached_property
    def upper_left_bbox(self):
        return {
            'north': self.most_northern,
            'south': self.most_southern + ((self.lat_span / METRES_PER_DEGREE) / 2),
            'west': self.most_western,
            'east': self.most_western + ((self.lng_span / METRES_PER_DEGREE) / 2),
        }

    @property
    def upper_left_collisions(self):
        return Collisions(
            data=[
                collision for collision in self if collision.is_in_place(self.upper_left_bbox)
            ]
        )

    @cached_property
    def upper_right_bbox(self):
        return {
            'north': self.most_northern,
            'south': self.most_southern + ((self.lat_span / METRES_PER_DEGREE) / 2),
            'west': self.most_western + ((self.lng_span / METRES_PER_DEGREE) / 2),
            'east': self.most_eastern,
        }

    @property
    def upper_right_collisions(self):
        return Collisions(
            data=[
                collision for collision in self if collision.is_in_place(self.upper_right_bbox)
            ]
        )

    @cached_property
    def lower_left_bbox(self):
        return {
            'north': self.most_southern + ((self.lat_span / METRES_PER_DEGREE) / 2),
            'south': self.most_southern,
            'west': self.most_western,
            'east': self.most_western + ((self.lng_span / METRES_PER_DEGREE) / 2),
        }

    @property
    def lower_left_collisions(self):
        return Collisions(
            data=[
                collision for collision in self if collision.is_in_place(self.lower_left_bbox)
            ]
        )

    @cached_property
    def lower_right_bbox(self):
        return {
            'north': self.most_southern + ((self.lat_span / METRES_PER_DEGREE) / 2),
            'south': self.most_southern,
            'west': self.most_western + ((self.lng_span / METRES_PER_DEGREE) / 2),
            'east': self.most_eastern,
        }

    @property
    def lower_right_collisions(self):
        return Collisions(
            data=[
                collision for collision in self if collision.is_in_place(self.lower_right_bbox)
            ]
        )

    def preload_graph(self, use_graph_cache=True):

        if use_graph_cache is False or network_cache.get('bbox', self) is None:

            if area_from_coords(self.bbox) > 1000000000:
                logger.debug('Graph too large to load, splitting: %s', self.bbox)

                if len(self.upper_left_collisions) > 1:
                    self.upper_left_collisions.preload_graph()

                if len(self.upper_right_collisions) > 1:
                    self.upper_right_collisions.preload_graph()

                if len(self.lower_left_collisions) > 1:
                    self.lower_left_collisions.preload_graph()

                if len(self.lower_right_collisions) > 1:
                    self.lower_right_collisions.preload_graph()

            else:
                logger.debug('No split necessary in loading graph: %s', self.bbox)
                try:
                    # TODO: depending on filters, might want to get different network. Only for geojson generation. If filter of vehicle_type being car / goods vehicle, use car, if bike / pedestrian, use all
                    #       will need to have the network_cache accept network types to split then
                    network = ox.graph_from_bbox(
                        self.most_northern,
                        self.most_southern,
                        self.most_eastern,
                        self.most_western,
                        network_type='all',
                        simplify=True
                    )
                    network_cache.set(
                        'bbox',
                        self,
                        network
                    )
                except Exception as ex:
                    logger.warning('Could not create graph %s: %s', self.bbox, ex)

    @staticmethod
    def from_file(filepath):
        data = None
        with open(filepath, 'r') as collisions_filepath:
            data = fast_json.loads(collisions_filepath.read())

        collisions = Collisions()
        for collision_dict in data:
            collisions.append(
                Collision.parse(
                    collision_dict
                )
            )

        return collisions

    @staticmethod
    def from_dir(dirpath):
        collisions = Collisions()
        for filename in glob.iglob(f'{dirpath}/**', recursive=True):
            if os.path.splitext(filename)[-1] != '.json':
                continue
            collisions.extend(
                Collisions.from_file(
                    filename
                )._data
            )

        return collisions

    @staticmethod
    def load_all():
        import road_collisions
        return Collisions.from_dir(
            os.path.join(road_collisions.__path__[0], 'resources')
        )

    def filter(self, **kwargs):
        '''
        By whatever props that exist
        '''
        logger.debug('Filtering from %s' % (len(self)))

        filtered = []
        for collision in self:
            valid = True
            for attr, val in kwargs.items():
                if getattr(collision, attr) != val:
                    valid = False
                    break
            if valid:
                filtered.append(collision)

        return Collisions(
            data=filtered,
            filters=kwargs,
            is_filtered=True
        )

    def inplace_filter(self, **kwargs):
        self.filters = kwargs
        if self.filters != {}:
            self._data = self.filter(**kwargs)._data
        self.is_filtered = True

    @property
    def gps_hash(self):
        if not self.is_filtered:
            self.inplace_filter(**self.filters)

        return hashlib.md5(
            str([
                point.gps.content_hash for point in self
            ]).encode()
        ).hexdigest()

    @staticmethod
    def split_collisions(collision):
        """
        Get the associated graph id and the give collision
        This can be then used to group collisions by graph

        :rtype: tuple
        """
        network = network_cache.get_at_point('bbox', collision)
        if network is not None:
            # this is slowing things down a lot, have a cache
            return get_graph_id(network), collision

        return None, None

    @property
    def network_collision_map(self):

        def get_mapping(graph_id_collisions):
            graph_id = graph_id_collisions[0]
            collisions = graph_id_collisions[1]
            return {
                'network': network_cache.get_by_id(graph_id),
                'collisions': collisions,
                'graph_id': graph_id
            }

        if not self.is_filtered:
            self.inplace_filter(**self.filters)

        maps = [Collisions.split_collisions(c) for c in self]
        maps = [m for m in maps if m[0] is not None]

        network_id_collisions_map = [
            (k, Collisions(data=[x for _, x in g])) for k, g in groupby(
                sorted([i for i in maps if i is not None], key=itemgetter(0)),
                itemgetter(0)
            )
        ]

        mapping_pool = ThreadPool(5)
        results = mapping_pool.map(get_mapping, network_id_collisions_map)
        mapping_pool.close()
        mapping_pool.join()

        network_collision_map = {}
        for map_data in results:
            network_collision_map[map_data['graph_id']] = {
                'network': map_data['network'],
                'collisions': map_data['collisions']
            }

        return network_collision_map

    @property
    def fp(self):
        filters = {k: v for k, v in self.filters.items() if v is not None}
        return os.path.join(
            GEOJSON_DIR,
            'collision_' + urllib.parse.urlencode(filters) + '.geojson'
        )

    @property
    def percent_collisions_outside_networks(self):
        """
        Return the % of collisions that are not within already cached networks
        """
        # Before preloading graph, see if we can get pretty much all points
        bad = 0
        good = 0
        for collision in self:
            at_point = network_cache.get_at_point('bbox', collision)
            if at_point is None:
                bad += 1
            else:
                good += 1

        if good == 0:
            if bad == 0:
                perc_bad = 0
            else:
                perc_bad = 100
        else:
            perc_bad = (bad / (good + bad)) * 100
            logger.debug('Missing %s%% of collisions', perc_bad)

        return perc_bad

    # want to get {edge_id: [collision, collision]}

    @property
    def edge_collision_map(self):

        data = defaultdict(Collisions)

        for _, network_collision_dict in self.network_collision_map.items():

            network = network_collision_dict['network']
            collisions = network_collision_dict['collisions']

            edges = nearest_edge.get(network, collisions)

            used_edges = []
            used_node_ids = []
            for edge in edges:
                # TODO: get closest, we just use the first
                used_edges.append(tuple(edge[0][0]))
                used_node_ids.extend(
                    [
                        edge[0][0][0],
                        edge[0][0][1]
                    ]
                )

            associated = list(zip(used_edges, collisions))

            for k, g in groupby(
                sorted(associated, key=itemgetter(0)),
                itemgetter(0)
            ):
                # TODO: are there ever overwrites?
                data[get_combined_id(k[0], k[1])] = Collisions(
                    data=[x for _, x in g]
                )

        return data

    @property
    def geojson(self):
        if os.path.exists(self.fp):
            with open(self.fp, 'r') as geojson_file:
                return fast_json.loads(geojson_file.read())

        if not self.is_filtered:
            self.inplace_filter(**self.filters)

        if self.percent_collisions_outside_networks > 2:
            logger.debug('Not all collision networks present, need to preload')

            self.preload_graph()

        geojson_features = []

        for _, network_collision_dict in self.network_collision_map.items():

            network = network_collision_dict['network']
            collisions = network_collision_dict['collisions']

            edges = nearest_edge.get(network, collisions)

            used_edges = []
            used_node_ids = []
            for edge in edges:
                # TODO: get closest, we just use the first
                used_edges.append(tuple(edge[0][0]))
                used_node_ids.extend(
                    [
                        edge[0][0][0],
                        edge[0][0][1]
                    ]
                )

            associated = list(zip(used_edges, collisions))
            edge_feature_map = {
                get_combined_id(k[0], k[1]): {
                    'danger': Collisions(
                        data=[x for _, x in g]
                    ).danger
                } for k, g in groupby(
                    sorted(associated, key=itemgetter(0)),
                    itemgetter(0)
                )
            }

            if bounding_graph_gdfs_cache.get(get_graph_id(network)) is None:
                gdfs_graph = ox.graph_to_gdfs(
                    network,
                    fill_edge_geometry=True
                )
                bounding_graph_gdfs_cache.set(
                    get_graph_id(network),
                    gdfs_graph
                )

            graph_nodes, graph_edges = bounding_graph_gdfs_cache.get(
                get_graph_id(network)
            )

            graph = ox.graph_from_gdfs(
                filter_nodes_from_geodataframe(graph_nodes, used_node_ids),
                filter_edges_from_geodataframe(graph_edges, used_edges)
            )

            update_edge_data(graph, edge_feature_map)

            features = geojson_from_graph(graph)['features']

            geojson_features.extend(features)

        geojson = {
            'type': 'FeatureCollection',
            'features': geojson_features
        }

        os.makedirs(GEOJSON_DIR, exist_ok=True)
        with open(self.fp, 'w') as geojson_file:
            geojson_file.write(fast_json.dumps(geojson))

        return geojson
