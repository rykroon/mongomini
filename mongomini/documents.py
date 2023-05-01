from dataclasses import dataclass
from typing import Any

from bson import ObjectId

from .dataclasses import (
    documentclass, delete_one, insert_one, is_documentclass, update_one, find
)
from .exceptions import MultipleObjectsReturned, ObjectDoesNotExist


class DocumentMeta(type):

    def __new__(metacls, name, bases, attrs):
        new_cls = super().__new__(metacls, name, bases, attrs)

        if name == 'Document' and not bases:
            # if Base Document, then just make a regular dataclass.
            return dataclass(new_cls)

        settings: type | None = attrs.pop('Settings', None)

        db = getattr(settings, 'db', None)
        collection_name = getattr(settings, 'collection_name', "")
        repr = getattr(settings, 'repr', True)
        eq = getattr(settings, 'eq', True)
        order = getattr(settings, 'order', False)

        new_cls = documentclass(
            db=db, collection_name=collection_name, repr=repr, eq=eq, order=order
        )(new_cls)
        return new_cls

    def __call__(self, *args, **kwargs):
        if not is_documentclass(self):
            raise TypeError(f"Can't instantiate abstract class '{self.__name__}'.")
        return super().__call__(*args, **kwargs)


class Document(metaclass=DocumentMeta):

    class Settings:
        ...

    _id: ObjectId | None = None

    @classmethod
    def find(cls, query: dict[str, Any]):
        return find(cls, query)

    @classmethod
    async def get(cls, query: dict[str, Any]):
        cursor = cls.find(query)
        try:
            result = await anext(cursor)

        except StopAsyncIteration as exc:
            raise ObjectDoesNotExist

        try:
            await anext(cursor)

        except StopAsyncIteration:
            return result

        raise MultipleObjectsReturned

    async def insert(self):
        return await insert_one(self)

    async def update(self, *fields):
        return await update_one(self, *fields)

    async def delete(self):
        return await delete_one(self)
