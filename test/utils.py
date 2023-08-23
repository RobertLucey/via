import re
import os

from gridfs import GridFS

from via.db import db
from via.settings import (
    MONGO_NETWORKS_COLLECTION,
    MONGO_RAW_JOURNEYS_COLLECTION,
    MONGO_PARSED_JOURNEYS_COLLECTION,
)

IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


def wipe_mongo():
    if not IS_ACTION:
        db.raw_journeys.drop()
        db.networks.drop()
        db.parsed_journeys.drop()
        for i in db.gridfs.find({"filename": {"$regex": f'^{re.escape("test_")}'}}):
            db.gridfs.delete(i._id)
