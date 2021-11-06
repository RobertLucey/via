import os
import threading
import datetime
from collections import defaultdict

import fast_json

import numpy as np
from rtree.index import Index as RTreeIndex
from shapely.geometry import Point

from osmnx import utils_graph

from via import logger
from via.settings import VERSION
from via.constants import EDGE_CACHE_DIR
from via.utils import get_combined_id, get_graph_id
from via.bounding_graph_gdfs_cache import utils_bounding_graph_gdfs_cache


GEOM_RTREE_CACHE = defaultdict(dict)


def nearest_edges(G, X, Y, return_dist=False):
    if not (hasattr(X, "__iter__") and hasattr(Y, "__iter__")):
        X = np.array([X])
        Y = np.array([Y])

    if np.isnan(X).any() or np.isnan(Y).any():  # pragma: no cover
        raise ValueError("`X` and `Y` cannot contain nulls")

    graph_id = get_graph_id(G)
    if graph_id in GEOM_RTREE_CACHE:
        geoms = GEOM_RTREE_CACHE[graph_id]['geoms']
        rtree = GEOM_RTREE_CACHE[graph_id]['rtree']
    else:
        if utils_bounding_graph_gdfs_cache.get(get_graph_id(G)) is None:
            utils_bounding_graph_gdfs_cache.set(
                get_graph_id(G),
                utils_graph.graph_to_gdfs(G, nodes=False)["geometry"]
            )

        geoms = utils_bounding_graph_gdfs_cache.get(get_graph_id(G))

        rtree = RTreeIndex()
        for pos, bounds in enumerate(geoms.bounds.values):
            rtree.insert(pos, bounds)

        GEOM_RTREE_CACHE[graph_id] = {
            'geoms': geoms,
            'rtree': rtree
        }

    ne_dist = list()
    for xy in zip(X, Y):
        dists = geoms.iloc[list(rtree.nearest(xy, num_results=12))].distance(Point(xy))

        used_edges = []
        edges = []
        distances = []
        for k, v in dists.to_dict().items():
            if get_combined_id(k[0], k[1]) not in used_edges:
                edges.append(k)
                distances.append(v)
                used_edges.append(get_combined_id(k[0], k[1]))

        ne_dist.append((edges, distances))

    ne, dist = zip(*ne_dist)

    return list(ne), list(dist)



class NearestEdgeCache():
    # TODO: split these in a grid of lat / lng 0.5 by the first gps of the upper right or something. Not very important as files are small
    # TODO: just store uuids as string so no silly casting

    def __init__(self):
        self.loaded = False
        self.data = {}
        self.last_save_len = -1
        self.last_saved_time = datetime.datetime.utcnow()
        self.saver()

    def saver(self):
        self.load()

        if all([
            self.last_save_len < len(self.data),
            (datetime.datetime.utcnow() - self.last_saved_time).total_seconds() > 5
        ]):
            self.save()

        saver = threading.Timer(
            10,
            self.saver
        )
        saver.daemon = True
        saver.start()

    def save(self):
        logger.debug(f'Saving cache {self.fp}')
        with open(self.fp, 'w') as f:
            f.write(fast_json.dumps(self.data))
        self.last_save_len = len(self.data)
        self.last_saved_time = datetime.datetime.utcnow()

    def get(self, graph, frames):
        """

        :param graph:
        :param frames: list of frames to get nearest edges of
        :return: list of list of edge ids or tuple of edge_id and distance.
            Each frame having its own list of closest few roads
        """

        self.load()

        # FIXME: should use frame hash rather than gps hash as we want context too
        frame_ids_to_get = [
            str(frame.gps_hash) for frame in frames if self.data.get(str(frame.gps_hash), None) is None
        ]

        id_frame_map = {str(f.gps_hash): f for f in frames}

        requested_frame_edge_map = {
            str(f.gps_hash): self.data.get(str(f.gps_hash), None) for f in frames
        }

        if frame_ids_to_get != []:
            results = nearest_edges(
                graph,
                [id_frame_map[frame_id].gps.lng for frame_id in frame_ids_to_get],
                [id_frame_map[frame_id].gps.lat for frame_id in frame_ids_to_get],
                return_dist=True
            )

            frame_id_result_map = dict(
                zip(
                    frame_ids_to_get,
                    list(
                        zip(
                            results[0],
                            results[1]
                        )
                    )
                )
            )

            for frame_id, edge_data in frame_id_result_map.items():
                edge_data = list(edge_data)
                self.data[frame_id] = list(zip(edge_data[0], edge_data[1]))

        requested_frame_edge_map = {
            str(f.gps_hash): self.data.get(str(f.gps_hash), None) for f in frames
        }

        return list(requested_frame_edge_map.values())

    def load(self):
        if self.loaded:
            return

        logger.debug(f'Loading cache {self.fp}')
        if not os.path.exists(self.fp):
            os.makedirs(
                os.path.dirname(self.fp),
                exist_ok=True
            )
            self.save()
        with open(self.fp, 'r') as f:
            self.data = fast_json.loads(f.read())
        self.loaded = True
        self.last_save_len = len(self.data)

    @property
    def fp(self):
        # TODO: split by lat lng regions
        return os.path.join(EDGE_CACHE_DIR, VERSION, 'cache.json')


nearest_edge = NearestEdgeCache()
