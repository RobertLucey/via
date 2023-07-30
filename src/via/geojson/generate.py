import operator
import datetime

from via import logger
from via.settings import MONGO_PARSED_JOURNEYS_COLLECTION
from via.utils import (
    get_journeys,
    should_include_journey,
    get_mongo_interface,
)
from via.models.journeys import Journeys


def get_generation_config(
    transport_type: str = None,
    version: str = None,
    version_op: str = None,
    earliest_time: int = None,
    latest_time: int = None,
    place: str = None,
) -> dict:
    config = []
    if transport_type in {None, "all"}:
        config = [
            {
                "transport_type": "all",
                "name": "all",
                "version": version,
                "version_op": version_op if version else None,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "place": place,
            },
            {
                "transport_type": "bike",
                "name": "bike",
                "version": version,
                "version_op": version_op if version else None,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "place": place,
            },
            {
                "transport_type": "car",
                "name": "car",
                "version": version,
                "version_op": version_op if version else None,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "place": place,
            },
            {
                "transport_type": "bus",
                "name": "bus",
                "version": version,
                "version_op": version_op if version else None,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "place": place,
            },
        ]
    else:
        config = [
            {
                "transport_type": transport_type,
                "name": transport_type,
                "version": version,
                "version_op": version_op if version else None,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "place": place,
            }
        ]

    return config


def generate_geojson(
    transport_type: str,
    version: str = False,
    version_op: str = None,
    earliest_time: int = None,
    latest_time: int = None,
    place: str = None,
) -> dict:
    logger.info(
        "Generating geojson: transport_type=%s version=%s version_op=%s earliest_time=%s latest_time=%s place=%s",
        transport_type,
        version,
        version_op,
        earliest_time,
        latest_time,
        place,
    )

    for config_item in get_generation_config(
        transport_type=transport_type,
        version=version,
        version_op=version_op,
        earliest_time=earliest_time,
        latest_time=latest_time,
        place=place,
    ):
        logger.info('Generating geojson for "%s"', config_item["transport_type"])

        journeys = get_journeys(
            transport_type=config_item["transport_type"],
            earliest_time=earliest_time,
            latest_time=latest_time,
        )

        journeys = Journeys(
            data=[
                journey
                for journey in journeys
                if should_include_journey(
                    journey,
                    version_op=getattr(operator, version_op)
                    if version_op is not None
                    else None,
                    version=version,
                )
            ]
        )

        mongo_interface = get_mongo_interface()

        getattr(mongo_interface, MONGO_PARSED_JOURNEYS_COLLECTION).delete_many(
            {
                "journey_type": config_item["name"],
                "geojson_version": config_item["version"],
                "geojson_version_op": config_item["version_op"],
                "geojson_earliest_time": config_item["earliest_time"],
                "geojson_latest_time": config_item["latest_time"],
                "geojson_place": config_item["place"],
            }
        )

        data = None

        if len(journeys):
            data = journeys.geojson

            data["journey_type"] = config_item["name"]
            data["geojson_version"] = config_item["version"]
            data["geojson_version_op"] = config_item["version_op"]
            data["geojson_earliest_time"] = config_item["earliest_time"]
            data["geojson_latest_time"] = config_item["latest_time"]
            data["place"] = config_item["place"]
            data["save_time"] = datetime.datetime.utcnow().timestamp()

            getattr(mongo_interface, MONGO_PARSED_JOURNEYS_COLLECTION).insert_one(data)

        return data
