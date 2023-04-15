from dataclasses import asdict, dataclass, field
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCursor
import pymongo

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .meta import DocumentMeta
from .utils import include


class Document(metaclass=DocumentMeta):
    
    class Settings:
        abstract = True

    _id: ObjectId = field(default_factory=ObjectId)
 
    @classmethod
    def from_document(cls, document: dict[str, Any]):
        init_kwargs = {f: document[f] for f in cls._meta.init_fields if f in document}
        obj = cls(**init_kwargs)

        for f in cls._meta.non_init_fields:
            if f not in document:
                continue
            setattr(obj, f, document[f])

        return obj

    @classmethod
    def find(cls, query: dict[str, Any]) -> AsyncIOMotorCursor:
        cursor = cls._meta.collection.find(filter=query)
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
        document = asdict(self)
        if document['_id'] is None:
            del document['_id']

        result = await self.__class__._meta.collection.insert_one(document)
        if self._id is None:
            self._id = result.inserted_id

        assert result.inserted_id == self._id

    async def update(self, *fields):
        dict_factory = include(*fields) if fields else dict
        document = asdict(self, dict_factory=dict_factory)
        result = await self.__class__._meta.collection.update_one(
            filter={"_id": self._id}, update={"$set": document}
        )
        assert result.matched_count == 1
        assert result.modified_count == 1

    async def delete(self):
        result = await self.__class__._meta.collection.delete_one({"_id": self._id})
        assert result.deleted_count == 1


@dataclass
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
