from dataclasses import dataclass, asdict, fields
from functools import lru_cache
from typing import Callable, Iterable

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCursor


_COLLECTION = '__mongomini_collection__'


def documentclass(
    cls=None, /, *,
    db: AsyncIOMotorDatabase | None = None,
    collection_name: str = "",
    repr: bool = True,
    eq: bool = True,
    order: bool = False
):

    def wrap(cls):
        return _process_class(cls, db, collection_name, repr, eq, order)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)


def _process_class(cls, db, collection_name, repr, eq, order):
    # get parent db if db is None.
    if db is None:
        for base in reversed(cls.mro()):
            if not is_documentclass(base):
                continue
            db = getattr(base, _COLLECTION)

    assert db is not None, "A database is required."
    collection_name = collection_name or cls.__name__.lower()
    collection = db[collection_name]
    setattr(cls, _COLLECTION, collection)
    new_cls = dataclass(repr=repr, eq=eq, order=order, kw_only=True)(cls)
    assert any(f.name == '_id' for f in fields(new_cls)), "Missing '_id' field."
    return new_cls


def is_documentclass(obj):
    """
        Returns True if the obj is a a documentclass or an instance of a
        documentclass.
    """
    cls = obj if isinstance(obj, type) else type(obj)
    return hasattr(cls, _COLLECTION)


def _is_documentclass_instance(obj):
    """
        Returns True if the obj is an instance of a documentclass.
    """
    return hasattr(type(obj), _COLLECTION)


def include(*fields: str) -> Callable[[Iterable], dict]:
    """
        Returns a dict_factory that will include the fields.
    """
    def include_dict_factory(iterable: Iterable) -> dict:
        return {k: v for k, v in iterable if k in fields}
    return include_dict_factory


def exclude(*fields: str) -> Callable[[Iterable], dict]:
    """
        Returns a dict_factory that will exclude the fields.
    """
    def exclude_dict_factory(iterable: Iterable) -> dict:
        return {k: v for k, v in iterable if k not in fields}
    return exclude_dict_factory


async def insert_one(obj, /):
    """
        Insert an instance of a documentclass into its collection.
    """
    if not _is_documentclass_instance(obj):
        raise TypeError("Must be called with a documentclass instance.")

    document = asdict(obj)
    if document['_id'] is None:
        del document['_id']

    collection = getattr(obj, _COLLECTION)
    result = await collection.insert_one(document)
    obj._id = result.inserted_id
    return result


async def update_one(obj, /, *fields):
    """
        Update an instance of a documentclass.
    """
    if not _is_documentclass_instance(obj):
        raise TypeError("Must be called with a documentclass instance.")

    dict_factory = include(*fields) if fields else dict
    document = asdict(obj, dict_factory=dict_factory)
    collection = getattr(obj, _COLLECTION)
    return await collection.update_one(filter={"_id": obj._id}, update={"$set": document})


async def delete_one(obj, /):
    """
        Delete an instance of a documentclass from the Collection.
    """
    if not _is_documentclass_instance(obj):
        raise TypeError("Must be called with a documentclass instance.")

    collection = getattr(obj, _COLLECTION)
    return await collection.delete_one({"_id": obj._id})


async def find_one(cls, query):
    """
        Return a single instance that matches the query on the documentclass or None.
    """
    if not is_documentclass(cls):
        raise TypeError("Must be called with a documentclass type or instance.")

    collection = getattr(cls, _COLLECTION)
    return await collection.find_one(query)


def find(cls, query) -> AsyncIOMotorCursor:
    """
        Performs a query on the documentclass.
        Returns a DocumentCursor.
    """
    if not is_documentclass(cls):
        raise TypeError("Must be called with a documentclass type or instance.")

    collection = getattr(cls, _COLLECTION)
    return collection.find(filter=query)


@lru_cache
def _get_init_and_non_init_fields(cls: type) -> tuple[list[str], list[str]]:
    init_fields = []
    non_init_fields = []
    for field in fields(cls):
        if field.init:
            init_fields.append(field.name)
        else:
            non_init_fields.append(field.name)
    return init_fields, non_init_fields


def fromdict(cls, data: dict):
    """
        Attempts to create an instance of a documentclass from a dictionary.
    """
    if not is_documentclass(cls):
        raise TypeError("Must be called with a documentclass type or instance.")

    init_fields, non_init_fields = _get_init_and_non_init_fields(cls)
    init_kwargs = {f: data[f] for f in init_fields if f in data}
    obj = cls(**init_kwargs)

    for field in non_init_fields:
        if field not in data:
            continue
        setattr(obj, field, data[field])

    return obj
