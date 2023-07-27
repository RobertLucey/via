import os
import time
import stat
import datetime

from via.settings import MAX_GEOJSON_AGE, MONGO_PARSED_JOURNEYS_COLLECTION
from via.utils import read_json, get_mongo_interface
from via.geojson.utils import generate_basename


def get_geojson(
    journey_type,
    earliest_time=None,
    latest_time=None,
    place=None,
    version=None,
    version_op=None
):
    # TODO: react to version/version_op/earliest_time/latest_time

    if journey_type is None:
        journey_type = "all"

    db = get_mongo_interface()
    data = getattr(db, MONGO_PARSED_JOURNEYS_COLLECTION).find_one(
        {
            'journey_type': journey_type,
            'save_time': {'$gt': (datetime.datetime.utcnow() - datetime.timedelta(seconds=MAX_GEOJSON_AGE)).timestamp()},
            'place': place
        }
    )
    if not data:
        raise FileNotFoundError()  # Quick hack

    data['_id'] = str(data['_id'])

    return data
