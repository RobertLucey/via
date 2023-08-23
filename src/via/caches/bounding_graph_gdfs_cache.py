from typing import Any
import pickle

from cachetools.func import ttl_cache

from gridfs import GridFS

from via.utils import get_mongo_interface
from via.settings import GRIDFS_BOUNDING_GRAPH_GDFS_GRAPH_FILENAME_PREFIX


class BoundingGraphGDFSGraphs:
    def __init__(self):
        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    @staticmethod
    def get_filename(key):
        return f"{GRIDFS_BOUNDING_GRAPH_GDFS_GRAPH_FILENAME_PREFIX}_{key}"

    @ttl_cache(maxsize=50, ttl=60 * 60)
    def get_from_gridfs(self, key):
        return pickle.loads(
            self.grid.find_one({"filename": self.get_filename(key)}).read()
        )

    def get(self, key: Any):
        if self.grid.find_one({"filename": self.get_filename(key)}):
            return self.get_from_gridfs(key)

        return None

    def set(self, key: Any, value: Any):
        if self.get(key):
            return None

        self.grid.put(pickle.dumps(value), filename=self.get_filename(key))


bounding_graph_gdfs_cache = BoundingGraphGDFSGraphs()
