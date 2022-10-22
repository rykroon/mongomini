from dataclasses import asdict, fields, is_dataclass
from functools import cached_property
import inspect

from bson.objectid import ObjectId

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned


class ObjectManager:

    def __init__(self, class_, collection):
        if not is_dataclass(class_):
            raise TypeError("Class is not a dataclass.")

        if not inspect.isclass(class_):
            raise TypeError("Class is not a class.")

        self.class_ = class_
        self.collection = collection

        assert '_id' in self.field_names, "Dataclass must have an '_id' field."

    @cached_property
    def fields(self):
        return fields(self.class_)

    @cached_property
    def field_names(self):
        return tuple([f.name for f in self.fields])

    def find(self, query):
        cursor = self.collection.find(query)
        return ObjectIterator(cursor, self)

    async def get(self, query):
        cursor = self.collection.find(query)

        try:
            document = await cursor.next()

        except StopAsyncIteration:
            raise ObjectDoesNotExist

        try:
            await cursor.next()

        except StopAsyncIteration:
            ...

        else:
            raise MultipleObjectsReturned

        return self._from_document(document)

    async def insert(self, obj, /):
        if obj._id is None:
            obj._id = ObjectId()

        document = asdict(obj)
        return await self.collection.insert_one(document)

    async def update(self, obj, /):
        filter_ = {'_id': obj._id}
        update = {
            '$set': asdict(obj)
        }
        return await self.collection.update_one(filter_, update)

    async def delete(self, obj, /):
        return await self.delete_by_id(obj._id)

    async def delete_by_id(self, _id, /):
        filter_ = {'_id': _id}
        return await self.collection.delete_one(filter_)

    def _from_document(self, document: dict):
        kwargs = {f: document[f] for f in self.field_names if f in document}
        return self.class_(**kwargs)


class ObjectIterator:

    def __init__(self, cursor, manager):
        self.cursor = cursor
        self.manager = manager

    def __aiter__(self):
        return self

    async def __anext__(self):
        document = await self.cursor.next()
        obj = self.manager._from_document(document)
        return obj
