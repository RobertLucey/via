from typing import Any
import pickle

from cachetools.func import ttl_cache

from gridfs import GridFS

from via.db import db
from via.settings import NXMAP_FILENAME_PREFIX


class NXMapCache:
    def __init__(self):
        self.grid = GridFS(db.client)

    @staticmethod
    def get_filename(key):
        return f"{NXMAP_FILENAME_PREFIX}_{key}"

    @ttl_cache(maxsize=10, ttl=60 * 60)
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


nxmap_cache = NXMapCache()
