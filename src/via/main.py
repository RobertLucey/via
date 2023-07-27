import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from pymongo import MongoClient
from typing import List, Optional, Union

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
    db = get_mongo_interface()

    result = getattr(db, MONGO_RAW_JOURNEYS_COLLECTION).find_one({"uuid": raw_journey.uuid})

    if not result:
        # Store the complete raw journey:
        getattr(db, MONGO_RAW_JOURNEYS_COLLECTION).insert_one(raw_journey.dict())

        # Parse it into some GeoJSON to store:
        journey = Journey(
            data=raw_journey.dict()["data"],
            is_culled=True,
            transport_type=raw_journey.transport_type,
            suspension=raw_journey.suspension,
            version=raw_journey.version,
        )

        #db.parsed_journeys.insert_one(journey.geojson)
    return {"status": "inserted" if not result else "already exists"}


@app.get("/get_raw_journeys")
async def get_raw_journeys(page: int = Query(1, gt=0), page_size: int = Query(5, gt=0)):
    """
    Exposes raw journey data so others running via can
    get data from many hosts
    """
    # TODO: better pagination

    db = get_mongo_interface()

    data = list(getattr(db, MONGO_RAW_JOURNEYS_COLLECTION).find({}).skip((page - 1) * page_size).limit(page_size))

    for obj in data:
        obj["_id"] = str(obj["_id"])

    return data


@app.get("/get_journey")
async def get_journey():
    """
    Simply grabs a random journey from Mongo.
    """
    db = get_mongo_interface()

    res = getattr(db, MONGO_PARSED_JOURNEYS_COLLECTION).find_one()

    # Make the ID a string so it's returnable:
    res["_id"] = str(res["_id"])

    return res


# TODO: Update this endpoint name and support time ranges/coords
@app.get("/get_geojson")
async def get_all_journeys(earliest_time: str = None, latest_time: str = None, place: str = None):
    """
    Fetch all the parsed journeys from the database between earliest/latest and
    return them as one GeoJSON FeatureCollection.
    """

    from via.geojson import (
        generate,
        retrieve
    )

    data = None
    try:
        data = retrieve.get_geojson(
            "bike",
            earliest_time=earliest_time,
            latest_time=latest_time,
            place=place
        )
    except FileNotFoundError:
        logger.info('geojson not found, generating')
        try:
            generate.generate_geojson(
                'bike',
                earliest_time=earliest_time,
                latest_time=latest_time,
                place=place
            )
        except Exception as ex:
            logger.error(f'Could not generate geojson: {ex}')
        else:
            data = retrieve.get_geojson(
                'bike',
                earliest_time=earliest_time,
                latest_time=latest_time,
                place=place
            )

    return data
