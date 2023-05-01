from dataclasses import dataclass as stdlib_dataclass, asdict, fields

from motor.motor_asyncio import AsyncIOMotorDatabase
from .utils import include, get_collection, set_collection


def dataclass(
    cls=None, /, *, db: AsyncIOMotorDatabase | None = None, collection_name: str = "", **kwargs
):

    def wrap(cls):
        return _process_class(cls, db, collection_name, **kwargs)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)


def _process_class(cls, db, collection_name, **kwargs):
    collection = None if db is None else db[collection_name or cls.__name__.lower()]
    set_collection(cls, collection)
    new_cls = stdlib_dataclass(kw_only=True, **kwargs)(cls)
    # The only requirement is that there is a field called "_id".
    assert any(f.name == '_id' for f in fields(new_cls)), "Missing '_id' field."
    return new_cls


async def insert_one(obj, /):
    document = asdict(obj)
    if document['_id'] is None:
        del document['_id']

    collection = get_collection(obj)
    result = await collection.insert_one(document)
    obj._id = result.inserted_id
    return result


async def update_one(obj, /, *fields):
    dict_factory = include(*fields) if fields else dict
    document = asdict(obj, dict_factory=dict_factory)
    collection = get_collection(obj)
    return await collection.update_one(filter={"_id": obj._id}, update={"$set": document})


async def delete_one(obj, /):
    collection = get_collection(obj)
    return await collection.delete_one({"_id": obj._id})


async def find_one(cls, query):
    ...


def find(cls, query):
    ...
