from dataclasses import dataclass, asdict, fields
from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCursor
import pymongo


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
    cls = obj if isinstance(obj, type) else type(obj)
    return hasattr(cls, _COLLECTION)


def _is_documentclass_instance(obj):
    return hasattr(type(obj), _COLLECTION)


def include(*fields: str):
    def include_dict_factory(iterable):
        return {k: v for k, v in iterable if k in fields}
    return include_dict_factory


def exclude(*fields: str):
    def exclude_dict_factory(iterable):
        return {k: v for k, v in iterable if k not in fields}
    return exclude_dict_factory


async def insert_one(obj, /):
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
    if not _is_documentclass_instance(obj):
        raise TypeError("Must be called with a documentclass instance.")

    dict_factory = include(*fields) if fields else dict
    document = asdict(obj, dict_factory=dict_factory)
    collection = getattr(obj, _COLLECTION)
    return await collection.update_one(filter={"_id": obj._id}, update={"$set": document})


async def delete_one(obj, /):
    if not _is_documentclass_instance(obj):
        raise TypeError("Must be called with a documentclass instance.")

    collection = getattr(obj, _COLLECTION)
    return await collection.delete_one({"_id": obj._id})


async def find_one(cls, query):
    if not is_documentclass(cls):
        raise TypeError("Must be called with a documentclass type or instance.")

    collection = getattr(cls, _COLLECTION)
    return await collection.find_one(query)


def find(cls, query):
    if not is_documentclass(cls):
        raise TypeError("Must be called with a documentclass type or instance.")
    collection = getattr(cls, _COLLECTION)
    cursor = collection.find(filter=query)
    return DocumentCursor(cls, cursor)


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


def from_document(cls, document: dict):
    if not is_documentclass(cls):
        raise TypeError("Must be called with a documentclass type or instance.")

    init_fields, non_init_fields = _get_init_and_non_init_fields(cls)
    init_kwargs = {f: document[f] for f in init_fields if f in document}
    obj = cls(**init_kwargs)

    for field in non_init_fields:
        if field not in document:
            continue
        setattr(obj, field, document[field])

    return obj


@dataclass(eq=False, slots=True, frozen=True)
class DocumentCursor:

    document_class: type
    cursor: AsyncIOMotorCursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        document = await anext(self.cursor)
        return from_document(self.document_class, document)

    def limit(self, limit: int):
        self.cursor.limit(limit)

    def skip(self, skip: int):
        self.cursor.skip(skip)

    def sort(self, *fields: str):
        field_list = [
            (f, pymongo.ASCENDING)
            if not f.startswith('-')
            else (f[1:], pymongo.DESCENDING)
            for f in fields
        ]
        self.cursor.sort(field_list)
