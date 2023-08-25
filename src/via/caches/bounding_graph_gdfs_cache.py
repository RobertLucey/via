from typing import Any
import pickle

from cachetools.func import ttl_cache

from gridfs import GridFS

from via.settings import GRIDFS_BOUNDING_GRAPH_GDFS_GRAPH_FILENAME_PREFIX
from via.db import db
from via.settings import MAX_CACHE_SIZE


class BoundingGraphGDFSGraphs:
    @staticmethod
    def get_filename(key):
        return f"{GRIDFS_BOUNDING_GRAPH_GDFS_GRAPH_FILENAME_PREFIX}_{key}"

    @ttl_cache(maxsize=MAX_CACHE_SIZE, ttl=60 * 60)
    def get_from_gridfs(self, key):
        return pickle.loads(
            db.gridfs.find_one({"filename": self.get_filename(key)}).read()
        )

    def get(self, key: Any):
        if db.gridfs.find_one({"filename": self.get_filename(key)}):
            return self.get_from_gridfs(key)

        return None

    def set(self, key: Any, value: Any):
        if self.get(key):
            return None

        db.gridfs.put(pickle.dumps(value), filename=self.get_filename(key))


bounding_graph_gdfs_cache = BoundingGraphGDFSGraphs()
