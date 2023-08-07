import pickle
import datetime
from cachetools.func import ttl_cache

import osmnx as ox
from gridfs import GridFS
from networkx.classes.multidigraph import MultiDiGraph

from via import logger
from via.settings import MONGO_NETWORKS_COLLECTION, GRIDFS_NETWORK_FILENAME_PREFIX
from via.utils import is_within, get_graph_id, get_mongo_interface
from via.place_cache import place_cache


def get_filename(graph_id):
    return f"{GRIDFS_NETWORK_FILENAME_PREFIX}_{graph_id}"


class NetworkCache:
    def __init__(self):
        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    @ttl_cache(maxsize=50, ttl=60 * 60)
    def _get_from_mongo(self, graph_id: int) -> MultiDiGraph:
        return pickle.loads(
            self.grid.find_one({"filename": get_filename(graph_id)}).read()
        )

    def get_from_mongo(self, graph_id: int) -> MultiDiGraph:
        """

        :param graph_id:
        :return:
        :rtype: MultiDiGraph
        """
        result = self.grid.find_one({"filename": get_filename(graph_id)})

        if not result:
            return None

        return self._get_from_mongo(graph_id)

    def put_to_mongo(self, network: MultiDiGraph, bbox: dict):
        """

        :param network:
        :param bbox:
        """
        graph_id = get_graph_id(network)

        self.grid.put(pickle.dumps(network), filename=get_filename(graph_id))

        # bbox as coords rather than network as network bbox is smaller and wouldn't match when trying to get for a journey
        getattr(self.mongo_interface, MONGO_NETWORKS_COLLECTION).insert_one(
            {
                "graph_id": graph_id,
                "type": "bbox",
                "bbox": bbox,
                "insert_time": datetime.datetime.utcnow().timestamp(),
            }
        )

    def get(self, journey) -> MultiDiGraph:
        """

        :param journey:
        :return:
        :rtype: MultiDiGraph
        """
        candidates = []
        network_configs = list(
            getattr(self.mongo_interface, MONGO_NETWORKS_COLLECTION).find(
                {
                    "insert_time": {
                        "$gt": datetime.datetime.utcnow().timestamp()
                        - 60 * 60 * 12  # TODO: to config
                    }
                }
            )
        )
        for network_config in network_configs:
            if is_within(journey.bbox, network_config["bbox"]):
                candidates.append((network_config["graph_id"], network_config["bbox"]))

        if candidates:
            logger.debug(
                "%s: Using a larger network rather than generating", journey.gps_hash
            )
            return self.get_from_mongo(candidates[0][0])

        if place_cache.get_by_bbox(journey.bbox) is not None:
            bbox = place_cache.get_by_bbox(journey.bbox)["bbox"]

            network = ox.graph_from_bbox(
                bbox["north"],
                bbox["south"],
                bbox["east"],
                bbox["west"],
                network_type=journey.network_type,
                simplify=True,
            )

            self.put_to_mongo(network, bbox)
            return network

        return None

    def set(self, network: MultiDiGraph, bbox: dict):
        """

        :param network:
        :param bbox:
        """
        graph_id = get_graph_id(network)

        if not getattr(self.mongo_interface, MONGO_NETWORKS_COLLECTION).find_one(
            {
                "graph_id": graph_id,
                "insert_time": {
                    "$gt": datetime.datetime.utcnow().timestamp()
                    - 60 * 60 * 12  # TODO: to config
                },
            }
        ):
            self.put_to_mongo(network, bbox)


network_cache = NetworkCache()
