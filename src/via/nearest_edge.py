import os
import threading
import datetime
from collections import defaultdict

import numpy as np
from rtree.index import Index as RTreeIndex
from shapely.geometry import Point
from gridfs import GridFS

from osmnx import utils_graph

from via import logger
from via.settings import VERSION
from via.utils import (
    get_combined_id,
    get_graph_id,
    read_json,
    write_json,
    get_mongo_interface,
)
from via.bounding_graph_gdfs_cache import utils_bounding_graph_gdfs_cache


GEOM_RTREE_CACHE = defaultdict(dict)


# NOTE: This was pulled from osmnx and modified
def nearest_edges(G, X, Y, return_dist=False):
    if not (hasattr(X, "__iter__") and hasattr(Y, "__iter__")):
        X = np.array([X])
        Y = np.array([Y])

    if np.isnan(X).any() or np.isnan(Y).any():  # pragma: no cover
        raise ValueError("`X` and `Y` cannot contain nulls")

    graph_id = get_graph_id(G)
    if graph_id in GEOM_RTREE_CACHE:
        geoms = GEOM_RTREE_CACHE[graph_id]["geoms"]
        rtree = GEOM_RTREE_CACHE[graph_id]["rtree"]
    else:
        if utils_bounding_graph_gdfs_cache.get(get_graph_id(G)) is None:
            utils_bounding_graph_gdfs_cache.set(
                get_graph_id(G), utils_graph.graph_to_gdfs(G, nodes=False)["geometry"]
            )

        geoms = utils_bounding_graph_gdfs_cache.get(get_graph_id(G))

        rtree = RTreeIndex()
        for pos, bounds in enumerate(geoms.bounds.values):
            rtree.insert(pos, bounds)

        GEOM_RTREE_CACHE[graph_id] = {"geoms": geoms, "rtree": rtree}

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


class NearestEdgeCache:
    # TODO: split these in a grid of lat / lng 0.5 by the first gps of the upper right or something. Not very important as files are small

    def __init__(self):
        self.data = {}
        self.cached_hashes = set()

        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    def get(self, graph, frames):
        # TODO: first go through the data and see if we can skip any there

        if len(frames) == 1 and frames[0].gps_hash in self.cached_hashes:
            return [self.data[frames[0].gps_hash]]

        gps_hashes = [f.gps_hash for f in frames]

        outside_cache = set(gps_hashes) - self.cached_hashes

        if outside_cache:
            found_keys = self.mongo_interface.nearest_edge_cache.find(
                {"gps_hash": {"$in": list(outside_cache)}}, {"gps_hashes": 1}
            )
            found_keys = set(doc["gps_hashes"] for doc in found_keys)
            missing_keys = set(gps_hashes) - found_keys

            frame_ids_to_get = missing_keys

            if frame_ids_to_get != []:
                id_frame_map = {f.gps_hash: f for f in frames}

                results = nearest_edges(
                    graph,
                    [id_frame_map[frame_id].gps.lng for frame_id in frame_ids_to_get],
                    [id_frame_map[frame_id].gps.lat for frame_id in frame_ids_to_get],
                    return_dist=True,
                )

                frame_id_result_map = dict(
                    zip(frame_ids_to_get, list(zip(results[0], results[1])))
                )

                for frame_id, edge_data in frame_id_result_map.items():
                    edge_data = list(edge_data)
                    self.data[frame_id] = list(
                        zip(edge_data[0], edge_data[1])
                    )  # FIXME Setting here. To mongo
                    self.cached_hashes.add(frame_id)

        return [self.data.get(f.gps_hash, None) for f in frames]


nearest_edge = NearestEdgeCache()
