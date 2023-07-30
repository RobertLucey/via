import datetime

from via.settings import MAX_GEOJSON_AGE, MONGO_PARSED_JOURNEYS_COLLECTION
from via.utils import get_mongo_interface


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

    mongo_interface = get_mongo_interface()
    data = getattr(mongo_interface, MONGO_PARSED_JOURNEYS_COLLECTION).find_one(
        {
            "journey_type": journey_type,
            "save_time": {
                "$gt": (
                    datetime.datetime.utcnow()
                    - datetime.timedelta(seconds=MAX_GEOJSON_AGE)
                ).timestamp()
            },
            "place": place,
        }
    )
    if not data:
        raise FileNotFoundError()  # Quick hack

    data["_id"] = str(data["_id"])

    return data
