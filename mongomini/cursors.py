from dataclasses import dataclass
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorCursor

from .dataclasses import from_document


@dataclass(eq=False, slots=True)
class DocumentCursor:

    document_class: type
    cursor: AsyncIOMotorCursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        document = await anext(self.cursor)
        return from_document(self.document_class, document)

    def limit(self, limit: int):
        self.cursor.limit(limit)

    def skip(self, skip: int):
        self.cursor.skip(skip)

    def sort(self, *fields: str):
        field_list = [
            (f, ASCENDING)
            if not f.startswith('-')
            else (f[1:], DESCENDING)
            for f in fields
        ]
        self.cursor.sort(field_list)
