import os
import time
import stat

from via.constants import GEOJSON_DIR
from via.settings import MAX_GEOJSON_AGE
from via.utils import read_json
from via.geojson.utils import generate_basename


def get_geojson(
    journey_type,
    earliest_time=None,
    latest_time=None,
    place=None,
    version=None,
    version_op=None,
    max_age=None,
):
    if journey_type is None:
        journey_type = "all"

    basename = generate_basename(
        name=journey_type,
        version=version,
        version_op=version_op,
        earliest_time=earliest_time,
        latest_time=latest_time,
        place=place,
    )
    geojson_file = os.path.join(GEOJSON_DIR, f"{basename}.geojson")

    if not os.path.exists(geojson_file):
        raise FileNotFoundError()

    if max_age is None:
        max_age = MAX_GEOJSON_AGE

    if time.time() - os.stat(geojson_file)[stat.ST_MTIME] > max_age:
        raise FileNotFoundError()

    return read_json(geojson_file)
