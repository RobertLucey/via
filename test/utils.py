import re
import os


from via.db import db

IS_ACTION = os.environ.get("IS_ACTION", "False") == "True"


def wipe_mongo():
    if not IS_ACTION:
        db.raw_journeys.drop()
        db.networks.drop()
        for i in db.gridfs.find({"filename": {"$regex": f'^{re.escape("test_")}'}}):
            db.gridfs.delete(i._id)
