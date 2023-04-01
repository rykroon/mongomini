from dataclasses import asdict, dataclass, field, fields
from typing import ClassVar, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor
import pymongo

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned


CollectionType = ClassVar[AsyncIOMotorCollection]


@dataclass(kw_only=True)
class Document:
    _collection: CollectionType
    _id: ObjectId = field(default_factory=ObjectId)

    @classmethod
    def from_document(cls, document: dict[str, Any]):
        init_fields = []
        non_init_fields = []
        for field in fields(cls):
            (non_init_fields, init_fields)[field.init].append(field.name)

        params = {f: document[f] for f in init_fields if f in document}
        obj = cls(**params)
        [setattr(obj, f, document[f]) for f in non_init_fields if f in document]
        return obj

    @classmethod
    def find(cls, query: dict[str, Any]) -> AsyncIOMotorCursor:
        cursor = cls._collection.find(filter=query)
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
        result = await self._collection.insert_one(asdict(self))
        assert result.inserted_id == self._id

    async def update(self):
        result = await self._collection.update_one(
            filter={"_id": self._id}, update={"$set": asdict(self)}
        )
        assert result.matched_count == 1
        assert result.modified_count == 1

    async def delete(self):
        result = await self._collection.delete_one({"_id": self._id})
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
        field_list =[
            (f, pymongo.ASCENDING)
            if not f.startswith('-')
            else (f[1:], pymongo.DESCENDING)
            for f in fields
        ]
        self.cursor.sort(field_list)
