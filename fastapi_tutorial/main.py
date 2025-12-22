from enum import Enum

from fastapi import FastAPI, Query

from pydantic import BaseModel

from typing import Annotated

from pydantic import AfterValidator

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None



app = FastAPI()

def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
    return id



@app.get("/")
async def root():
    return {"message": "Hello World"}

# Tutorial: https://fastapi.tiangolo.com/tutorial/path-params/ ----------------------------------------

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}



# Tutorial: https://fastapi.tiangolo.com/tutorial/query-params/ ----------------------------------------
# http://127.0.0.1:8000/items/?skip=0&limit=10

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


# mutated as query-params-str-validations uses the same endpoint / method
@app.get("/items-basic/")
async def read_items(q: str | None = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


# Tutorial: https://fastapi.tiangolo.com/tutorial/body/ ----------------------------------------

@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}

# Tutorial: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/ ----------------------------------------
@app.get("/items/")
async def read_items(
    q: Annotated[
        list[str] | None, 
        Query(
            title="Query string", 
            description="Minimum length of query string is 3", 
            min_length=3, 
            alias="item-query", 
            deprecated=True,
        ),
    ] = None,
    id: Annotated[str | None, AfterValidator(check_valid_id)] = None,
):
# async def read_items(q: Annotated[list[str] | None, Query(title="Query string", description="Minimum length of query string is 3", min_length=3, alias="item-query", deprecated=True,),] = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results
# http://localhost:8000/items/?q=foo&q=bar q may appear multiple times

