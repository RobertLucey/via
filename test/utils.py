import re
import os

from gridfs import GridFS

from via.utils import get_mongo_interface
from via.settings import (
    MONGO_NETWORKS_COLLECTION,
    MONGO_RAW_JOURNEYS_COLLECTION,
    MONGO_PARSED_JOURNEYS_COLLECTION,
)

IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


def wipe_mongo():
    if not IS_ACTION:
        mongo_interface = get_mongo_interface()
        getattr(mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION).drop()
        getattr(mongo_interface, MONGO_NETWORKS_COLLECTION).drop()
        getattr(mongo_interface, MONGO_PARSED_JOURNEYS_COLLECTION).drop()
        grid = GridFS(mongo_interface)
        for i in grid.find({"filename": {"$regex": f'^{re.escape("test_")}'}}):
            grid.delete(i._id)
