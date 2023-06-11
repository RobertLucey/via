from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.get("/")
async def root():
    return {
        "message": "Hello world",
    }


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/offset_items/")
async def read_item_with_offset(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]


@app.post("/items/")
async def create_item(item: Item):
    return item
