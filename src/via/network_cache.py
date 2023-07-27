import datetime
import logging
import os
import pickle
import threading
from cachetools.func import ttl_cache

import osmnx as ox
from gridfs import GridFS
from networkx.classes.multidigraph import MultiDiGraph

from via import logger
from via.settings import MONGO_NETWORKS_COLLECTION
from via.utils import (
    is_within,
    area_from_coords,
    get_graph_id,
    get_mongo_interface
)
from via.place_cache import place_cache


class NetworkCache:
    def __init__(self):
        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    @ttl_cache(maxsize=50, ttl=360)
    def get_from_mongo(self, graph_id):
        return pickle.loads(
            self.grid.find_one(
                {
                    'filename': f"network_{graph_id}"
                }
            ).read()
        )

    def put_to_mongo(self, network, bbox):
        graph_id = get_graph_id(network)

        self.grid.put(pickle.dumps(network), filename=f'network_{graph_id}')

        # bbox as coords rather than network as network bbox is smaller and wouldn't match when trying to get for a journey
        getattr(self.mongo_interface, MONGO_NETWORKS_COLLECTION).insert_one(
            {
                "graph_id": graph_id,
                "type": 'bbox',
                "bbox": bbox
            }
        )

    def get(self, journey) -> MultiDiGraph:
        candidates = []
        network_configs = list(getattr(self.mongo_interface, MONGO_NETWORKS_COLLECTION).find())
        for network_config in network_configs:
            if is_within(journey.bbox, network_config["bbox"]):
                candidates.append((network_config['graph_id'], network_config['bbox']))

        if candidates != []:
            logger.debug(
                f"{journey.gps_hash}: Using a larger network rather than generating"
            )
            selection = sorted(
                candidates, key=lambda x: area_from_coords(x[1])
            )[0]

            return self.get_from_mongo(candidates[0][0])

        if place_cache.get_by_bbox(journey.bbox) is not None:
            bbox = place_cache.get_by_bbox(journey.bbox)["bbox"]

            network = ox.graph_from_bbox(
                bbox["north"],
                bbox["south"],
                bbox["east"],
                bbox["west"],
                network_type="all",
                simplify=True,
            )

            self.put_to_mongo(network, bbox)

            return network

        return None

    def set(self, network: MultiDiGraph, bbox: dict):
        graph_id = get_graph_id(network)

        if not getattr(self.mongo_interface, MONGO_NETWORKS_COLLECTION).find_one({'graph_id': graph_id}):
            self.put_to_mongo(network, bbox)


network_cache = NetworkCache()
