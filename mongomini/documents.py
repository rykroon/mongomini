from dataclasses import dataclass
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCursor
import pymongo

from .dataclasses import insert_one, update_one, delete_one
from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .meta import DocumentMeta
from .utils import get_init_field_names, get_non_init_field_names, get_collection


class Document(metaclass=DocumentMeta):

    class Settings:
        abstract = True

    _id: ObjectId | None = None

    @classmethod
    def from_document(cls, document: dict[str, Any]):
        init_kwargs = {f: document[f] for f in get_init_field_names(cls) if f in document}
        obj = cls(**init_kwargs)

        for f in get_non_init_field_names(cls):
            if f not in document:
                continue
            setattr(obj, f, document[f])

        return obj

    @classmethod
    def find(cls, query: dict[str, Any]) -> AsyncIOMotorCursor:
        collection = get_collection(cls)
        cursor = collection.find(filter=query)
        return DocumentCursor(cls, cursor)

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


@dataclass(eq=False)
class DocumentCursor:

    class_: type[Document]
    cursor: AsyncIOMotorCursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        document = await anext(self.cursor)
        return self.class_.from_document(document)

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
