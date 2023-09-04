import threading
import traceback
from typing import List, Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from via import logger
from via.models.journey import Journey
from via.db import db
from via.constants import EMPTY_GEOJSON


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

    result = db.raw_journeys.find_one({"uuid": raw_journey.uuid})

    if not result:
        # Validate
        Journey(
            data=raw_journey.dict()["data"],
            transport_type=raw_journey.transport_type,
            suspension=raw_journey.suspension,
            version=raw_journey.version,
        )

        db.raw_journeys.insert_one(raw_journey.dict())
        return JSONResponse(status_code=201, content={"message": "created"})
    else:
        return JSONResponse(status_code=409, content={"message": "already exists"})


@app.get("/get_raw_journey")
async def get_raw_journey(journey_uuid: str = None):
    journey = db.raw_journeys.find_one({"uuid": journey_uuid})
    journey["_id"] = str(journey["_id"])
    return journey


@app.get("/get_journey_uuids")
async def get_raw_journey_uuids():
    data = db.raw_journeys.find({}, {"uuid": 1, "_id": 0})

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
    except LookupError:
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
            return {
                "message": f"Could not generate geojson: {ex}",
                "traceback": traceback.format_exc(),
            }
        else:
            try:
                data = retrieve.get_geojson(
                    "bike",
                    earliest_time=earliest_time,
                    latest_time=latest_time,
                    place=place,
                )
            except LookupError:
                # Likely no data
                return EMPTY_GEOJSON

    return data


def start_geojson_generate(first_run):
    from via.geojson import generate

    threading.Timer(60 * 60, start_geojson_generate, (False,)).start()
    if not first_run:
        # Don't do on startup
        generate.generate_geojson(
            "bike",
        )


threading.Thread(target=start_geojson_generate, args=(True,)).start()
