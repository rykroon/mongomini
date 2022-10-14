from dataclasses import asdict, fields
from functools import cached_property

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .utils import Exclude


class QueryManager:

    def __init__(self, class_, collection):
        self.class_ = class_
        self.collection = collection

    @cached_property
    def fields(self):
        return fields(self.class_)

    @cached_property
    def field_names(self):
        return [f.name for f in self.fields]

    def find(self, query):
        cursor = self.collection.find(query)
        return ObjectIterator(cursor, self.class_)

    async def get(self, query):
        cursor = self.collection.find(query)

        try:
            result = await cursor.next()

        except StopAsyncIteration:
            raise ObjectDoesNotExist

        try:
            await cursor.next()

        except StopAsyncIteration:
            ...

        else:
            raise MultipleObjectsReturned

        return self._from_document(result)


    async def insert(self, obj, /):
        document = asdict(obj, dict_factory=Exclude('_id'))
        result = await self.collection.insert_one(document)
        assert result.acknowledged
        self._id = result.inserted_id

    async def update(self, obj, /):
        query = {'_id': obj._id}
        update = {'$set': asdict(obj)}
        result = await self.collection.update_one(query, update)
        assert result.acknowledged
        assert result.matched_count == 1
        assert result.modified_count == 1

    async def delete(self, obj, /):
        result = await self.delete_by_id(obj._id)

    async def delete_by_id(self, _id, /):
        query = {'_id': _id}
        result = await self.collection.delete_one(query)
        assert result.acknowledged
        assert result.deleted_count == 1

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
        document = await self._cursor.next()
        return self.manager._from_document(document)