import operator
import datetime
import time

import ujson

from via import logger
from via.utils import (
    get_journeys,
    should_include_journey,
)
from via.settings import GEOJSON_FILENAME_PREFIX
from via.models.journeys import Journeys
from via.db import db


GENERATING = []


def generate_geojson(
    transport_type: str,
    version: str = False,
    version_op: str = None,
    earliest_time: int = None,
    latest_time: int = None,
    place: str = None,
) -> dict:
    start = time.monotonic()

    logger.info(
        "Generating geojson: transport_type=%s version=%s version_op=%s earliest_time=%s latest_time=%s place=%s",
        transport_type,
        version,
        version_op,
        earliest_time,
        latest_time,
        place,
    )

    config = {
        "transport_type": "bike",
        "name": "bike",
        "version": version,
        "version_op": version_op if version else None,
        "earliest_time": earliest_time,
        "latest_time": latest_time,
        "place": place,
    }

    if config in GENERATING:
        logger.info("Already generating: %s", config)
        return

    GENERATING.append(config)

    try:
        logger.info('Generating geojson for "%s"', config["transport_type"])

        journeys = get_journeys(
            transport_type=config["transport_type"],
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

        data = None

        if len(journeys):
            data = journeys.geojson

            present = db.gridfs.find(
                {
                    "metadata.journey_type": config["name"],
                    "metadata.geojson_version": config["version"],
                    "metadata.geojson_version_op": config["version_op"],
                    "metadata.geojson_earliest_time": config["earliest_time"],
                    "metadata.geojson_latest_time": config["latest_time"],
                    "metadata.geojson_place": config["place"],
                }
            )

            for obj in list(present):
                db.gridfs.delete(obj._id)

            meta = {}
            meta["journey_type"] = config["name"]
            meta["geojson_version"] = config["version"]
            meta["geojson_version_op"] = config["version_op"]
            meta["geojson_earliest_time"] = config["earliest_time"]
            meta["geojson_latest_time"] = config["latest_time"]
            meta["geojson_place"] = config["place"]
            meta["save_time"] = datetime.datetime.utcnow().timestamp()

            db.gridfs.put(
                ujson.dumps(data).encode("utf8"),
                metadata=meta,
                filename=GEOJSON_FILENAME_PREFIX + "_" + ujson.dumps(meta),
            )

    finally:
        GENERATING.remove(config)

    logger.info(
        "Generated geojson in %s seconds: transport_type=%s version=%s version_op=%s earliest_time=%s latest_time=%s place=%s",
        time.monotonic() - start,
        transport_type,
        version,
        version_op,
        earliest_time,
        latest_time,
        place,
    )

    return data
