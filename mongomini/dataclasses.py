from dataclasses import dataclass, asdict, fields

from motor.motor_asyncio import AsyncIOMotorDatabase
from .utils import include, get_init_field_names, get_non_init_field_names


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
            db = get_collection(base)

    assert db is not None, "A database is required."
    collection_name = collection_name or cls.__name__.lower()
    collection = db[collection_name]
    set_collection(cls, collection)
    new_cls = dataclass(repr=repr, eq=eq, order=order, kw_only=True)(cls)
    assert any(f.name == '_id' for f in fields(new_cls)), "Missing '_id' field."
    return new_cls


def is_documentclass(obj):
    cls = obj if isinstance(obj, type) else type(obj)
    return hasattr(cls, _COLLECTION)


def _is_document_instance(obj):
    return hasattr(type(obj), _COLLECTION)


def get_collection(obj):
    return getattr(obj, _COLLECTION)


def set_collection(obj, collection):
    setattr(obj, _COLLECTION, collection)


async def insert_one(obj, /):
    if not _is_document_instance(obj):
        raise TypeError

    document = asdict(obj)
    if document['_id'] is None:
        del document['_id']

    collection = get_collection(obj)
    result = await collection.insert_one(document)
    obj._id = result.inserted_id
    return result


async def update_one(obj, /, *fields):
    if not _is_document_instance(obj):
        raise TypeError

    dict_factory = include(*fields) if fields else dict
    document = asdict(obj, dict_factory=dict_factory)
    collection = get_collection(obj)
    return await collection.update_one(filter={"_id": obj._id}, update={"$set": document})


async def delete_one(obj, /):
    if not _is_document_instance(obj):
        raise TypeError

    collection = get_collection(obj)
    return await collection.delete_one({"_id": obj._id})


async def find_one(cls, query):
    if not is_documentclass(cls):
        raise TypeError
    
    collection = get_collection(cls)
    return await collection.find_one(query)


def find(cls, query):
    ...


def from_document(cls, document: dict):
    if not is_documentclass(cls):
        raise TypeError

    init_kwargs = {f: document[f] for f in get_init_field_names(cls) if f in document}
    obj = cls(**init_kwargs)

    for f in get_non_init_field_names(cls):
        if f not in document:
            continue
        setattr(obj, f, document[f])

    return obj
