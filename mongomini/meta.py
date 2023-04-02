from dataclasses import dataclass
from functools import cached_property

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


@dataclass(kw_only=True)
class Meta:
    db: AsyncIOMotorDatabase
    collection_name: str | None = None

    def __get__(self, obj, objtype=None):
        if obj is not None:
            raise TypeError("Cannot access 'meta' from instance.")
        return self

    def __set_name__(self, owner, name):
        if self.collection_name is None:
            self.collection_name = owner.__name__.lower()

    @cached_property
    def collection(self) -> AsyncIOMotorCollection:
        return self.db[self.collection_name]
