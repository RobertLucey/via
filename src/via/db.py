import os

import pymongo
from gridfs import GridFS
from cached_property import cached_property

from via.settings import (
    MONGO_RAW_JOURNEYS_COLLECTION,
    MONGO_NETWORKS_COLLECTION,
)


class DB:
    def __init__(self, *args, **kwargs):
        self.url = kwargs.get("url", os.environ.get("MONGODB_URL", "localhost"))
        self.database = kwargs.get(
            "database", os.environ.get("MONGODB_DATABASE", "localhost")
        )

    @cached_property
    def client(self):
        return pymongo.MongoClient(self.url)[self.database]

    @cached_property
    def gridfs(self):
        return GridFS(self.client)

    @property
    def raw_journeys(self):
        return getattr(self.client, MONGO_RAW_JOURNEYS_COLLECTION)

    @property
    def networks(self):
        return getattr(self.client, MONGO_NETWORKS_COLLECTION)


db = DB()
