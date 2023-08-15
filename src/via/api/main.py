import threading
from typing import List, Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from via import logger
from via.settings import MONGO_RAW_JOURNEYS_COLLECTION, MONGO_PARSED_JOURNEYS_COLLECTION
from via.models.journey import Journey
from via.utils import get_mongo_interface


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RawJourneyDataPoint(BaseModel):
    acc: Union[float, int]
    gps: List[Union[int, float]]
    time: Optional[Union[float, int]] = None


class RawJourney(BaseModel):
    version: Optional[str] = "1.0"
    uuid: str
    device: str
    data: List[RawJourneyDataPoint]
    transport_type: Optional[str] = "bike"
    suspension: Optional[bool] = False
    is_partial: Optional[bool] = False


@app.post("/push_journey")
async def create_journey(raw_journey: RawJourney):
    """
    Simply dumps this journey into Mongo for now.
    """
    mongo_interface = get_mongo_interface()

    result = getattr(mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION).find_one(
        {"uuid": raw_journey.uuid}
    )

    if not result:
        # Validate
        Journey(
            data=raw_journey.dict()["data"],
            transport_type=raw_journey.transport_type,
            suspension=raw_journey.suspension,
            version=raw_journey.version,
        )

        getattr(mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION).insert_one(
            raw_journey.dict()
        )
    return {"status": "inserted" if not result else "already exists"}


@app.get("/get_raw_journey")
async def get_raw_journey(journey_uuid: str = None):
    journey = getattr(get_mongo_interface(), MONGO_RAW_JOURNEYS_COLLECTION).find_one(
        {"uuid": journey_uuid}
    )
    journey["_id"] = str(journey["_id"])
    return journey


@app.get("/get_journey_uuids")
async def get_raw_journey_uuids():
    mongo_interface = get_mongo_interface()

    data = getattr(mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION).find(
        {}, {"uuid": 1, "_id": 0}
    )

    return list([i["uuid"] for i in data])


# TODO: Update this endpoint name and support time ranges/coords
@app.get("/get_geojson")
async def get_all_journeys(
    earliest_time: str = None, latest_time: str = None, place: str = None
):
    """
    Fetch all the parsed journeys from the database between earliest/latest and
    return them as one GeoJSON FeatureCollection.
    """

    from via.geojson import generate, retrieve

    data = None
    try:
        data = retrieve.get_geojson(
            "bike", earliest_time=earliest_time, latest_time=latest_time, place=place
        )
    except FileNotFoundError:
        logger.info("geojson not found, generating")
        try:
            generate.generate_geojson(
                "bike",
                earliest_time=earliest_time,
                latest_time=latest_time,
                place=place,
            )
        except Exception as ex:
            logger.error("Could not generate geojson: %s", ex)
        else:
            data = retrieve.get_geojson(
                "bike",
                earliest_time=earliest_time,
                latest_time=latest_time,
                place=place,
            )

    return data


def start_geojson_generate(first_run):
    from via.geojson import generate

    threading.Timer(60 * 60 * 6, start_geojson_generate, (False,)).start()
    if not first_run:
        # Don't do on startup
        generate.generate_geojson(
            "bike",
        )


threading.Thread(target=start_geojson_generate, args=(True,)).start()
