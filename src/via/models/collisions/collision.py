import hashlib
import os
import json
import glob
from multiprocessing import Pool
from itertools import groupby
from operator import itemgetter

from cached_property import cached_property
from haversine import (
    haversine,
    Unit
)

import shapely
from networkx.readwrite import json_graph
import osmnx as ox

from road_collisions.models.raw_collision import RawCollision as BaseRawCollision
from road_collisions.models.collision import Collision as BaseCollision
from road_collisions.models.collision import Collisions as BaseCollisions

from via import logger
from via.nearest_edge import nearest_edge
from via.constants import METRES_PER_DEGREE
from via.utils import area_from_coords, get_graph_id, filter_nodes_from_geodataframe, filter_edges_from_geodataframe, update_edge_data, get_combined_id
from via.network_cache import network_cache
from via.models.gps import GPSPoint
from via.bounding_graph_gdfs_cache import bounding_graph_gdfs_cache


def geojson_from_graph(graph):
    json_links = json_graph.node_link_data(
        graph
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
        useless_properties = {
            'oneway',
            'length',
            'osmid',
            'highway',
            'source',
            'target',
            'key',
            'maxspeed',
            'lanes',
            'ref'
        }
        for useless_property in useless_properties:
            try:
                del feature['properties'][useless_property]
            except:
                pass
        geojson_features['features'].append(feature)

    return geojson_features


class Collision(BaseCollision):

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

    @property
    def danger(self):
        # FIXME: generally improve
        return len(self)

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

        if use_graph_cache is False or network_cache.get('bbox', self, poly=False) is None:

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
        with open(filepath, 'r') as f:
            data = json.loads(f.read())

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

        filtered = [
            d for d in self if all(
                [
                    getattr(d, attr) == kwargs[attr] for attr in kwargs.keys()
                ]
            )
        ]

        return Collisions(
            data=filtered
        )

    @property
    def gps_hash(self):
        return hashlib.md5(
            str([
                point.gps.content_hash for point in self
            ]).encode()
        ).hexdigest()

    @staticmethod
    def split_collisions(collision):
        try:
            network = network_cache.get_at_point('bbox', collision)
        except:
            logger.warning('Could not get network: %s' % (collision.serialize()))
        else:
            # this is slowing things down a lot, have a cache
            return get_graph_id(network), collision

    @property
    def geojson(self):

        geojson_features = []

        pool = Pool(processes=6)
        maps = pool.imap_unordered(Collisions.split_collisions, self)

        network_id_collisions_map = [
            (k, Collisions(data=[x for _, x in g])) for k, g in groupby(
                sorted([i for i in maps if i is not None], key=itemgetter(0)),
                itemgetter(0)
            )
        ]

        network_collision_map = {}
        for graph_id, collisions in network_id_collisions_map:
            network_collision_map[graph_id] = {
                'network': network_cache.get_by_id(graph_id),
                'collisions': collisions
            }

        for k, v in network_collision_map.items():

            network = v['network']
            collisions = v['collisions']

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
            edge_feature_map = dict([
                (get_combined_id(k[0], k[1]), {'danger': Collisions(data=[x for _, x in g]).danger}) for k, g in groupby(
                    sorted(associated, key=itemgetter(0)),
                    itemgetter(0)
                )
            ])

            if bounding_graph_gdfs_cache.get(get_graph_id(network)) is None:
                bounding_graph_gdfs_cache.set(
                    get_graph_id(network),
                    ox.graph_to_gdfs(
                        network,
                        fill_edge_geometry=True
                    )
                )
            graph_nodes, graph_edges = bounding_graph_gdfs_cache.get(
                get_graph_id(network)
            )

            ox.graph_to_gdfs(
                network,
                fill_edge_geometry=True
            )
            graph = ox.graph_from_gdfs(
                filter_nodes_from_geodataframe(graph_nodes, used_node_ids),
                filter_edges_from_geodataframe(graph_edges, used_edges)
            )

            update_edge_data(graph, edge_feature_map)

            geojson_features.append(geojson_from_graph(graph)['features'])

        return {
            'type': 'FeatureCollection',
            'features': geojson_features
        }