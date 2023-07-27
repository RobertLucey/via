from typing import Any
import pickle

from cachetools.func import ttl_cache

from gridfs import GridFS

from via.utils import get_mongo_interface


class UtilsBoundingGraphGDFSGraphs:
    def __init__(self, *args, **kwargs):
        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    @ttl_cache(maxsize=50, ttl=360)
    def get_from_gridfs(self, filename):
        return pickle.loads(self.grid.find_one({"filename": filename}).read())

    def get(self, key: Any):
        filename = f"utils_bounding_graph_gdfs_graph_{key}"

        if self.grid.find_one({"filename": filename}):
            return self.get_from_gridfs(filename)

    def set(self, k: Any, v: Any, skip_save: bool = False):
        if self.get(k):
            return

        self.grid.put(pickle.dumps(v), filename=f"utils_bounding_graph_gdfs_graph_{k}")


class BoundingGraphGDFSGraphs:
    def __init__(self, *args, **kwargs):
        self.mongo_interface = get_mongo_interface()
        self.grid = GridFS(self.mongo_interface)

    @ttl_cache(maxsize=50, ttl=360)
    def get_from_gridfs(self, filename):
        return pickle.loads(self.grid.find_one({"filename": filename}).read())

    def get(self, key: Any):
        filename = f"bounding_graph_gdfs_graph_{key}"

        if self.grid.find_one({"filename": filename}):
            return self.get_from_gridfs(filename)

    def set(self, k: Any, v: Any, skip_save: bool = False):
        if self.get(k):
            return

        self.grid.put(pickle.dumps(v), filename=f"bounding_graph_gdfs_graph_{k}")


bounding_graph_gdfs_cache = BoundingGraphGDFSGraphs()

utils_bounding_graph_gdfs_cache = UtilsBoundingGraphGDFSGraphs()
