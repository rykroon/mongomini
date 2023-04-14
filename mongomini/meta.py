from dataclasses import dataclass
from functools import cached_property
from itertools import chain

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase



@dataclass(kw_only=True, eq=False)
class Meta:
    db: AsyncIOMotorDatabase | None = None
    collection_name: str | None = None

    @cached_property
    def collection(self) -> AsyncIOMotorCollection | None:
        if self.db is None:
            return None
        return self.db[self.collection_name]


class DocumentMeta(type):

    def __new__(mcls, name, bases, attrs):
        mro: list[type] = list(chain.from_iterable([base.mro()[:-1] for base in bases]))
        settings: type | None = attrs.pop('Settings', None)
        meta: Meta = Meta()

        # loop through parent classes.
        parent_db = None
        for base in reversed(mro):
            if not isinstance(base, mcls):
                continue
            # inherit the parent's db.
            parent_db = base._meta.db

        meta.db = getattr(settings, 'db', parent_db)        
        meta.collection_name = getattr(settings, 'collection_name', name.lower())
        attrs['_meta'] = meta

        new_cls = super().__new__(mcls, name, bases, attrs)
        new_cls = dataclass(kw_only=True)(new_cls)
        return new_cls
