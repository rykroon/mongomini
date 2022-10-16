from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from functools import cached_property
import inspect
import itertools

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .utils import Include


class QueryManager:

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
        return [f.name for f in self.fields]

    @cached_property
    def _auto_now_fields(self):
        return [
            field.name
            for field in self.fields
            if field.metadata.get('auto_now') is True
        ]

    @cached_property
    def _auto_now_add_fields(self):
        return [
            field.name
            for field in self.fields
            if field.metadata.get('auto_now_add') is True
        ]

    @cached_property
    def _editable_fields(self):
        return [
            field.name
            for field in self.fields
            if field.metadata.get('editable', True) is True
        ]

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
        self._update_auto_now_add_fields(obj)
        document = asdict(obj)
        return await self.collection.insert_one(document)

    async def update(self, obj, /):
        self._update_auto_now_fields(obj)
        filter_ = {'_id': obj._id}
        update = {
            '$set': asdict(obj, dict_factory=Include(*self._editable_fields))
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

    def _update_auto_now_add_fields(self, obj):
        if not self._auto_now_add_fields and not self._auto_now_fields:
            return

        all_auto_now_fields = itertools.chain(
            self._auto_now_add_fields,
            self._auto_now_fields
        )
        now = datetime.utcnow()
        for field in all_auto_now_fields:
            setattr(obj, field, now)

    def _update_auto_now_fields(self, obj):
        if not self._auto_now_add_fields:
            return

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

        required = field.metadata.get('required')
        if required and bool(value) is False:
            raise ValueError

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
        document = await self.cursor.next()
        obj = self.manager._from_document(document)
        return obj