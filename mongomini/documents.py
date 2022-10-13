from dataclasses import dataclass, asdict, fields
from typing import ClassVar

from bson import ObjectId

from mongomini.utils import Exclude


@dataclass
class Document:

    collection: ClassVar = None

    _id: ObjectId = None

    @classmethod
    def new(cls, *args, **kwargs):
        obj = cls()
        obj.init(*args, **kwargs)
        return obj

    def init(self):
        ...

    async def pre_save(self):
        ...

    async def save(self):
        await self.pre_save()
        if self._id is None:
            return await self._insert()
        return await self._update()

    async def _insert(self):
        document = asdict(self, dict_factory=Exclude('_id'))
        result = await self.collection.insert_one(document)
        assert result.acknowledged
        self._id = result.inserted_id

    async def _update(self):
        query = {'_id': self._id}
        update = {'$set': asdict(self)}
        result = await self.collection.update_one(query, update)
        assert result.acknowledged
        assert result.matched_count == 1
        assert result.modified_count == 1


    async def delete(self):
        query = {'_id': self._id}
        result = await self.collection.delete_one(query)
        assert result.acknowledged
        assert result.deleted_count == 1
    