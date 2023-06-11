from fastapi import FastAPI
from pydantic import BaseModel
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


@app.get("/")
async def root():
    return {
        "message": "Hello world",
    }


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/offset_items")
async def read_item_with_offset(skip: int = 0, limit: int = 10):
    print(skip)
    print(limit)
    return fake_items_db[skip : skip + limit]


@app.post("/items/")
async def create_journey(journey: Journey):
    print(journey)
    return journey
