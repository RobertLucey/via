import os

from cached_property import cached_property

import pymongo

from via.settings import (
    MONGO_RAW_JOURNEYS_COLLECTION,
    MONGO_PARSED_JOURNEYS_COLLECTION,
    MONGO_NETWORKS_COLLECTION,
)


class DB:
    def __init__(self, *args, **kwargs):
        self.db_url = kwargs.get("db_url", os.environ.get("MONGODB_URL", "localhost"))
        self.database = kwargs.get(
            "database", os.environ.get("MONGODB_DATABASE", "localhost")
        )

    @cached_property
    def client(self):
        return pymongo.MongoClient(self.db_url)[self.database]

    @property
    def raw_journeys(self):
        return getattr(self.client, MONGO_RAW_JOURNEYS_COLLECTION)

    @property
    def parsed_journeys(self):
        return getattr(self.client, MONGO_PARSED_JOURNEYS_COLLECTION)

    @property
    def networks(self):
        return getattr(self.client, MONGO_NETWORKS_COLLECTION)


db = DB()
