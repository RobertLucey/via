import os

from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List

from via.models.journey import Journey

app = FastAPI()


class RawJourneyDataPoint(BaseModel):
    acc: float
    gps: List[float]
    time: float

class RawJourney(BaseModel):
    version: str
    uuid: str
    device: str
    data: List[RawJourneyDataPoint]
    transport_type: str
    suspension: bool
    is_partial: bool


def get_mongo_interface():
    """
    Returns the MongoDB DB interface. Here so it can be moved to utils.
    """
    db_url = os.environ.get("MONGODB_URL", None)

    client = MongoClient(db_url)
    return client[os.environ.get("MONGODB_DATABASE")]

@app.post("/push_journey")
async def create_journey(raw_journey: RawJourney):
    """
    Simply dumps this journey into Mongo for now.
    """
    db = get_mongo_interface()

    # Store the complete raw journey:
    db.raw_journeys.insert_one(raw_journey.dict())

    # Parse it into some GeoJSON to store:
    journey = Journey(
        data = raw_journey.dict()["data"],
        is_culled=True,
        transport_type=raw_journey.transport_type,
        suspension=raw_journey.suspension,
        version=raw_journey.version,
    )

    db.parsed_journeys.insert_one(journey.geojson)
    return {}


@app.get("/get_journey")
async def get_journey():
    """
    Simply grabs a random journey from Mongo.
    """
    db = get_mongo_interface()

    res = db.parsed_journeys.find_one()

    # Make the ID a string so it's returnable:
    res["_id"] = str(res["_id"])

    return res
