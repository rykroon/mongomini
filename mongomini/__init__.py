from dataclasses import asdict, dataclass, field, fields
from typing import ClassVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor


@dataclass(kw_only=True)
class Document:
    _collection: ClassVar[AsyncIOMotorCollection]
    _id: ObjectId = field(default_factory=ObjectId)

    @classmethod
    def from_document(cls, document: dict):
        field_names = set(f.name for f in fields(cls))
        fields_in_doc = field_names.intersection(document)
        params = {f: document[f] for f in fields_in_doc}
        return cls(**params)

    @classmethod
    def find(
        cls,
        query: dict | None = None,
        skip: int = 0,
        limit: int = 0,
        sort: list[tuple[str, int]] | None = None,
    ) -> AsyncIOMotorCursor:
        cursor = cls._collection.find(filter=query, skip=skip, limit=limit, sort=sort)
        return CursorWrapper(cls, cursor)

    @classmethod
    async def find_one(cls, **kwargs):
        document = await cls._collection.find_one(kwargs)
        if document is None:
            return None
        return cls.from_document(document)

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
class CursorWrapper:

    class_: type[Document]
    cursor: AsyncIOMotorCursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        document = await anext(self.cursor)
        return self.class_.from_document(document)

