import datetime
import re

import ujson

from via.settings import MAX_GEOJSON_AGE, GEOJSON_FILENAME_PREFIX
from via.db import db


def get_geojson(
    journey_type: str,
    earliest_time: int = None,
    latest_time: int = None,
    place: str = None,
    version: str = None,
    version_op: str = None,
) -> dict:
    # TODO: react to version/version_op/earliest_time/latest_time

    if journey_type is None:
        journey_type = "all"

    filename_pattern = re.compile(f"^{GEOJSON_FILENAME_PREFIX}")

    data = db.gridfs.find_one(
        {
            "filename": filename_pattern,
            "metadata.journey_type": journey_type,
            "metadata.save_time": {
                "$gt": (
                    datetime.datetime.utcnow()
                    - datetime.timedelta(seconds=MAX_GEOJSON_AGE)
                ).timestamp()
            },
            "metadata.place": place,
        }
    )
    if data is None:
        raise LookupError()

    data = ujson.loads(data.read())

    return data
