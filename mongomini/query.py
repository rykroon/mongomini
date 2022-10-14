from dataclasses import asdict, fields
from datetime import datetime
from functools import cached_property

from bson import ObjectId

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned


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

    @cached_property
    def _auto_now_fields(self):
        return [f.name for f in self.fields if f.metadata.get('auto_now') is True]

    @cached_property
    def _auto_now_add_fields(self):
        return [f.name for f in self.fields if f.metadata.get('auto_now_add') is True]

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
        if obj._id is None:
            obj._id = ObjectId()

        self._set_auto_now_add_fields(obj)
        document = asdict(obj)
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
        return await self.delete_by_id(obj._id)

    async def delete_by_id(self, _id, /):
        query = {'_id': _id}
        result = await self.collection.delete_one(query)
        assert result.acknowledged
        return result.deleted_count

    def _from_document(self, document: dict):
        kwargs = {f: document[f] for f in self.field_names if f in document}
        return self.class_(**kwargs)

    def _set_auto_now_add_fields(self, obj):
        all_auto_now_fields = self._auto_now_add_fields + self._auto_now_fields
        now = datetime.utcnow()
        for field in all_auto_now_fields:
            setattr(obj, field, now)

    def _set_auto_now_fields(self, obj):
        now = datetime.utcnow()
        for field in self._auto_now_fields:
            setattr(obj, field, now)

    def _validate(self, obj):
        for field in self.fields:
            self._validate_field(field, obj)

    def _validate_field(self, field, obj):
        value = getattr(obj, field.name)

        if not isinstance(value, field.type):
            raise TypeError

        choices = field.metadata.get('choices')
        if choices is not None:
            if value not in choices:
                raise ValueError


class ObjectIterator:

    def __init__(self, cursor, manager):
        self.cursor = cursor
        self.manager = manager

    def __aiter__(self):
        return self

    async def __anext__(self):
        document = await self._cursor.next()
        return self.manager._from_document(document)