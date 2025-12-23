import time

from enum import Enum

from fastapi import Cookie, FastAPI, HTTPException, Path, Query, Request

from fastapi.middleware.cors import CORSMiddleware

from http import HTTPStatus

from pydantic import AfterValidator, BaseModel, Field, HttpUrl, EmailStr

from typing import Annotated


class Tags(Enum):
    items = "items"
    meth_get = "get"
    meth_post = "post"
    meth_put = "put"
    meth_del = "delete"


class Image(BaseModel):
    url: HttpUrl
    name: str


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Fooohyoooo",
                    "description": "A very nice Item. Probably the best one you can find.",
                    "price": 35.4,
                    "tax": 3.2,
                }
            ]
        }
    }



app = FastAPI()

origins = [
    "http://localhost",
    "https://localhost",
    "http://localhost:8080",
    "https://localhost:8443",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

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
@app.get("/items/", tags=["items","get"])
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


# https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/ ----------------------------------------
# https://docs.python.org/3/library/http.html#http.HTTPStatus
@app.get(
    "/item/{item_id}",
    status_code=HTTPStatus.OK,
    tags=[Tags.items, Tags.meth_get],
    summary="Get an item by its int ID",
    # description="Get an item by its int ID and return the whole item representation if found.",
    response_description="The item representation retrieved by its ID",
    deprecated=True,
)
async def read_items(
    item_id: Annotated[int, Path(title="The ID of the item to get")],
    q: Annotated[str | None, Query(alias="item-query")] = None,
):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: [required](https://fastapi.tiangolo.com/tutorial/schema-extra-example/#required-and-optional-fields)
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    else:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="New item. Who dis?")
    return results