import os

from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


class JourneyDataPoint(BaseModel):
    acc: float
    gps: List[float]
    time: float

class Journey(BaseModel):
    version: str
    uuid: str
    device: str
    data: List[JourneyDataPoint]
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
async def create_journey(journey: Journey):
    """
    Simply dumps this journey into Mongo for now.
    """
    db = get_mongo_interface()

    db.journeys.insert_one(journey.dict())

    return {}


@app.get("/get_journey")
async def get_journey():
    """
    Simply grabs a random journey from Mongo.
    """
    db = get_mongo_interface()

    res = db.journeys.find_one()
    # Make the ID a string so it's returnable:
    res["_id"] = str(res["_id"])

    return res
